from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio

from app.database import get_db
from app.models.learning_task import LearningTask, QuizAttempt, PptGeneration
from app.models.graph_node import GraphNode
from app.models.source import Source
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskOut,
    QuizQuestionOut, QuizSubmission, QuizResultOut, QuizQuestionDetail,
    QuizAttemptOut, QuizGenerationStatusOut,
    PptSlide, PptGenerationOut, PptGenerationStatusOut,
)
from app.agents.quiz_agent import run_quiz_generation
from app.agents.ppt_agent import run_ppt_generation
from app.services.ppt_generator import save_ppt_as_html
from app.constants import MAX_TASKS, PASS_THRESHOLD, STAGE_COUNT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def _generate_quiz_background(
    attempt_id: int,
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
):
    """Background task to generate quiz questions."""
    from app.database import async_session
    
    async with async_session() as db:
        try:
            # Generate quiz via LLM with timeout
            questions = await asyncio.wait_for(
                run_quiz_generation(
                    node_name=node_name,
                    node_description=node_description,
                    source_content=source_content,
                    current_stage=current_stage,
                    difficulty=difficulty,
                ),
                timeout=90.0
            )
            
            if not questions:
                raise Exception("生成的题目为空")
            
            # Update attempt with questions
            attempt = (await db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))).scalar_one_or_none()
            if attempt:
                attempt.questions = questions
                attempt.status = "ready"
                await db.commit()
                logger.info(f"Quiz generation completed for attempt {attempt_id}")
        except asyncio.TimeoutError:
            logger.error(f"Quiz generation timeout for attempt {attempt_id}")
            attempt = (await db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))).scalar_one_or_none()
            if attempt:
                attempt.status = "failed"
                attempt.error = "生成超时，请稍后重试"
                await db.commit()
        except Exception as e:
            logger.error(f"Quiz generation failed for attempt {attempt_id}: {e}")
            attempt = (await db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))).scalar_one_or_none()
            if attempt:
                attempt.status = "failed"
                attempt.error = str(e)[:500]
                await db.commit()


async def _generate_ppt_background(
    generation_id: int,
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
):
    """Background task to generate PPT slides."""
    from app.database import async_session
    
    async with async_session() as db:
        try:
            slides = await asyncio.wait_for(
                run_ppt_generation(
                    node_name=node_name,
                    node_description=node_description,
                    source_content=source_content,
                    current_stage=current_stage,
                    difficulty=difficulty,
                ),
                timeout=120.0
            )
            
            if not slides:
                raise Exception("生成的幻灯片为空")
            
            ppt_title = f"{node_name} - PPT课件"
            if slides and slides[0].get("ppt_title"):
                ppt_title = slides[0]["ppt_title"]
            
            generation = (await db.execute(select(PptGeneration).where(PptGeneration.id == generation_id))).scalar_one_or_none()
            if generation:
                generation.title = ppt_title
                generation.slides = slides
                generation.status = "ready"
                
                try:
                    file_path = await save_ppt_as_html(
                        slides=slides,
                        ppt_id=generation_id,
                        title=ppt_title,
                        task_id=generation.task_id,
                    )
                    generation.file_path = file_path
                except Exception as save_error:
                    logger.error(f"Failed to save PPT HTML file: {save_error}")
                
                await db.commit()
                logger.info(f"PPT generation completed for generation {generation_id}")
        except asyncio.TimeoutError:
            logger.error(f"PPT generation timeout for generation {generation_id}")
            generation = (await db.execute(select(PptGeneration).where(PptGeneration.id == generation_id))).scalar_one_or_none()
            if generation:
                generation.status = "failed"
                generation.error = "生成超时，请稍后重试"
                await db.commit()
        except Exception as e:
            logger.error(f"PPT generation failed for generation {generation_id}: {e}")
            generation = (await db.execute(select(PptGeneration).where(PptGeneration.id == generation_id))).scalar_one_or_none()
            if generation:
                generation.status = "failed"
                generation.error = str(e)[:500]
                await db.commit()


async def _task_to_out(task: LearningTask, db: AsyncSession) -> TaskOut:
    """Convert LearningTask ORM to TaskOut with node_name resolved."""
    node_name = ""
    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if node:
        node_name = node.name
    return TaskOut(
        id=task.id,
        name=task.name,
        node_id=task.node_id,
        node_name=node_name,
        difficulty=task.difficulty,
        current_stage=task.current_stage,
        progress=task.progress,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=list[TaskOut])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LearningTask).order_by(LearningTask.created_at.desc()))
    tasks = result.scalars().all()
    return [await _task_to_out(t, db) for t in tasks]


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    # Check max tasks
    count = (await db.execute(select(func.count(LearningTask.id)))).scalar() or 0
    if count >= MAX_TASKS:
        raise HTTPException(400, f"最多只能创建 {MAX_TASKS} 个学习任务")

    # Validate node_id exists
    node = (await db.execute(select(GraphNode).where(GraphNode.id == body.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, f"知识节点 {body.node_id} 不存在")

    # Validate difficulty
    if body.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(400, "难度等级必须是 easy、medium 或 hard")

    task = LearningTask(
        name=body.name,
        node_id=body.node_id,
        difficulty=body.difficulty,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return await _task_to_out(task, db)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")
    return await _task_to_out(task, db)


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return await _task_to_out(task, db)


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    # Delete related quiz attempts
    attempts = (await db.execute(select(QuizAttempt).where(QuizAttempt.task_id == task_id))).scalars().all()
    for a in attempts:
        await db.delete(a)
    
    # Delete related PPT generations
    ppt_generations = (await db.execute(select(PptGeneration).where(PptGeneration.task_id == task_id))).scalars().all()
    for p in ppt_generations:
        await db.delete(p)
    
    # Flush to ensure related records are deleted before deleting the task
    await db.flush()

    await db.delete(task)
    await db.commit()
    return {"ok": True}


@router.post("/{task_id}/quiz/generate", response_model=QuizGenerationStatusOut, status_code=202)
async def generate_quiz(task_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start quiz generation asynchronously. Returns immediately with status."""
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    # Get node info
    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, "关联的知识节点不存在")

    # Get source content
    source_content = ""
    source = (await db.execute(select(Source).where(Source.id == node.source_id))).scalar_one_or_none()
    if source and source.content_text:
        source_content = source.content_text

    # Create QuizAttempt with status 'generating'
    attempt = QuizAttempt(
        task_id=task.id,
        stage_at_attempt=task.current_stage,
        questions=None,
        status="generating",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    # Start background task
    background_tasks.add_task(
        _generate_quiz_background,
        attempt_id=attempt.id,
        node_name=node.name,
        node_description=node.description or "",
        source_content=source_content,
        current_stage=task.current_stage,
        difficulty=task.difficulty,
    )

    return QuizGenerationStatusOut(
        attempt_id=attempt.id,
        status="generating",
        message="测验题目正在生成中，请查询状态接口获取结果"
    )


@router.get("/{task_id}/quiz/status", response_model=QuizAttemptOut)
async def get_quiz_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of quiz generation."""
    # Find the latest quiz attempt for this task
    attempt = (
        await db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.task_id == task_id)
            .order_by(QuizAttempt.created_at.desc())
        )
    ).scalar_one_or_none()

    if not attempt:
        raise HTTPException(404, "没有找到测验记录")

    # Build response based on status
    questions = None
    if attempt.status == "ready" and attempt.questions:
        questions = [
            QuizQuestionOut(index=i, question=q["question"], options=q["options"])
            for i, q in enumerate(attempt.questions)
        ]

    return QuizAttemptOut(
        id=attempt.id,
        task_id=attempt.task_id,
        stage_at_attempt=attempt.stage_at_attempt,
        status=attempt.status,
        questions=questions,
        error=attempt.error,
        created_at=attempt.created_at,
    )


@router.post("/{task_id}/quiz/submit", response_model=QuizResultOut)
async def submit_quiz(task_id: int, body: QuizSubmission, db: AsyncSession = Depends(get_db)):
    try:
        task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
        if not task:
            raise HTTPException(404, "学习任务不存在")

        # Find latest unanswered attempt
        attempt = (
            await db.execute(
                select(QuizAttempt)
                .where(QuizAttempt.task_id == task_id, QuizAttempt.answers.is_(None))
                .order_by(QuizAttempt.created_at.desc())
            )
        ).scalar_one_or_none()

        if not attempt:
            raise HTTPException(400, "没有待提交的测验，请先生成测验")
        
        # Check if quiz generation is complete
        if attempt.status != "ready":
            raise HTTPException(400, f"测验尚未生成完成，当前状态: {attempt.status}")

        questions = attempt.questions
        answers = body.answers

        logger.info(f"Submitting quiz: {len(answers)} answers for {len(questions)} questions")
        logger.info(f"Questions type: {type(questions)}")
        logger.info(f"First question: {questions[0] if questions else 'None'}")

        if len(answers) != len(questions):
            raise HTTPException(400, f"答案数量不匹配，预期 {len(questions)} 个")

        # Grade
        correct_count = 0
        details = []
        for i, q in enumerate(questions):
            user_answer = answers[i] if i < len(answers) else -1
            is_correct = user_answer == q["correct_index"]
            if is_correct:
                correct_count += 1
            details.append(QuizQuestionDetail(
                question=q["question"],
                options=q["options"],
                correct_index=q["correct_index"],
                user_answer=user_answer,
                is_correct=is_correct,
            ))

        score = correct_count / len(questions) if questions else 0
        passed = score >= PASS_THRESHOLD

        # Update attempt
        attempt.answers = answers
        attempt.score = score
        attempt.passed = passed
        await db.commit()
        logger.info(f"Quiz submitted successfully: score={score}, passed={passed}")

        return QuizResultOut(
            attempt_id=attempt.id,
            score=score,
            passed=passed,
            correct_count=correct_count,
            total=len(questions),
            details=details,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}", exc_info=True)
        raise HTTPException(500, f"提交测验时发生错误: {str(e)}")


@router.patch("/{task_id}/advance", response_model=TaskOut)
async def advance_stage(task_id: int, db: AsyncSession = Depends(get_db)):
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    # Check latest quiz passed
    latest_attempt = (
        await db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.task_id == task_id)
            .order_by(QuizAttempt.created_at.desc())
        )
    ).scalar_one_or_none()

    if not latest_attempt or not latest_attempt.passed:
        raise HTTPException(400, "最近一次测验未通过，无法升阶")

    if task.current_stage >= STAGE_COUNT - 1:
        # Already at max stage, mark completed
        task.progress = 100.0
        task.status = "completed"
    else:
        task.current_stage += 1
        task.progress = (task.current_stage + 1) * (100.0 / STAGE_COUNT)
        if task.current_stage >= STAGE_COUNT - 1:
            task.status = "completed"

    # Update associated GraphNode mastery
    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if node:
        node.mastery = min(1.0, task.progress / 100.0)

    await db.commit()
    await db.refresh(task)
    return await _task_to_out(task, db)


@router.post("/{task_id}/ppt/generate", response_model=PptGenerationStatusOut, status_code=202)
async def generate_ppt(task_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start PPT generation asynchronously. Returns immediately with status."""
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, "关联的知识节点不存在")

    source_content = ""
    source = (await db.execute(select(Source).where(Source.id == node.source_id))).scalar_one_or_none()
    if source and source.content_text:
        source_content = source.content_text

    generation = PptGeneration(
        task_id=task.id,
        title=f"{node.name} - PPT课件",
        slides=None,
        status="generating",
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    background_tasks.add_task(
        _generate_ppt_background,
        generation_id=generation.id,
        node_name=node.name,
        node_description=node.description or "",
        source_content=source_content,
        current_stage=task.current_stage,
        difficulty=task.difficulty,
    )

    return PptGenerationStatusOut(
        generation_id=generation.id,
        status="generating",
        message="PPT课件正在生成中，请查询状态接口获取结果"
    )


@router.get("/{task_id}/ppt/status", response_model=PptGenerationOut)
async def get_ppt_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of the latest PPT generation."""
    generation = (
        await db.execute(
            select(PptGeneration)
            .where(PptGeneration.task_id == task_id)
            .order_by(PptGeneration.created_at.desc())
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "没有找到 PPT 生成记录")

    slides = None
    if generation.status == "ready" and generation.slides:
        slides = [
            PptSlide(title=s.get("title", ""), content=s.get("content", ""), notes=s.get("notes"))
            for s in generation.slides
        ]

    return PptGenerationOut(
        id=generation.id,
        task_id=generation.task_id,
        title=generation.title,
        status=generation.status,
        slides=slides,
        file_path=generation.file_path,
        error=generation.error,
        created_at=generation.created_at,
    )


@router.get("/{task_id}/ppt", response_model=list[PptGenerationOut])
async def list_ppt(task_id: int, db: AsyncSession = Depends(get_db)):
    """List all PPT generations for a task."""
    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    generations = (
        await db.execute(
            select(PptGeneration)
            .where(PptGeneration.task_id == task_id)
            .order_by(PptGeneration.created_at.desc())
        )
    ).scalars().all()

    result = []
    for generation in generations:
        slides = None
        if generation.status == "ready" and generation.slides:
            slides = [
                PptSlide(title=s.get("title", ""), content=s.get("content", ""), notes=s.get("notes"))
                for s in generation.slides
            ]
        result.append(PptGenerationOut(
            id=generation.id,
            task_id=generation.task_id,
            title=generation.title,
            status=generation.status,
            slides=slides,
            file_path=generation.file_path,
            error=generation.error,
            created_at=generation.created_at,
        ))

    return result


@router.get("/{task_id}/ppt/{ppt_id}", response_model=PptGenerationOut)
async def get_ppt_detail(task_id: int, ppt_id: int, db: AsyncSession = Depends(get_db)):
    """Get PPT generation detail by ID."""
    generation = (
        await db.execute(
            select(PptGeneration).where(PptGeneration.id == ppt_id, PptGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "PPT 不存在")

    slides = None
    if generation.status == "ready" and generation.slides:
        slides = [
            PptSlide(title=s.get("title", ""), content=s.get("content", ""), notes=s.get("notes"))
            for s in generation.slides
        ]

    return PptGenerationOut(
        id=generation.id,
        task_id=generation.task_id,
        title=generation.title,
        status=generation.status,
        slides=slides,
        file_path=generation.file_path,
        error=generation.error,
        created_at=generation.created_at,
    )


@router.get("/{task_id}/ppt/{ppt_id}/download")
async def download_ppt(task_id: int, ppt_id: int, db: AsyncSession = Depends(get_db)):
    """Download PPT HTML file."""
    from fastapi.responses import FileResponse
    import os

    generation = (
        await db.execute(
            select(PptGeneration).where(PptGeneration.id == ppt_id, PptGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "PPT 不存在")

    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(404, "PPT 文件不存在")

    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in generation.title)
    filename = f"{safe_title}.html"

    return FileResponse(
        path=generation.file_path,
        filename=filename,
        media_type="text/html",
    )


async def _generate_content_background(
    generation_id: int,
    task_id: int,
    content_type: str,
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
):
    """Background task to generate content."""
    from app.database import async_session
    from app.models.learning_task import VideoGeneration, AnimationGeneration, PodcastGeneration, MindmapGeneration
    from app.services.content_generators import save_content_as_html

    agent_map = {
        'video': 'run_video_generation',
        'animation': 'run_animation_generation',
        'podcast': 'run_podcast_generation',
        'mindmap': 'run_mindmap_generation',
    }

    model_map = {
        'video': VideoGeneration,
        'animation': AnimationGeneration,
        'podcast': PodcastGeneration,
        'mindmap': MindmapGeneration,
    }

    data_field_map = {
        'video': 'script',
        'animation': 'concept',
        'podcast': 'script',
        'mindmap': 'nodes',
    }

    Model = model_map[content_type]

    async with async_session() as db:
        try:
            # Import agent function with better error handling
            try:
                agent_module = __import__(f'app.agents.{content_type}_agent', fromlist=[agent_map[content_type]])
                agent_func = getattr(agent_module, agent_map[content_type])
            except (ImportError, AttributeError) as import_error:
                logger.error(f"Failed to import agent for {content_type}: {import_error}")
                generation = (await db.execute(select(Model).where(Model.id == generation_id))).scalar_one_or_none()
                if generation:
                    generation.status = "failed"
                    generation.error = f"Agent导入失败: {str(import_error)}"
                    await db.commit()
                return

            try:
                content_data = await asyncio.wait_for(
                    agent_func(
                        node_name=node_name,
                        node_description=node_description,
                        source_content=source_content,
                        current_stage=current_stage,
                        difficulty=difficulty,
                    ),
                    timeout=180.0
                )
            except asyncio.TimeoutError:
                logger.error(f"{content_type} generation timeout for generation {generation_id}")
                generation = (await db.execute(select(Model).where(Model.id == generation_id))).scalar_one_or_none()
                if generation:
                    generation.status = "failed"
                    generation.error = "生成超时，请稍后重试"
                    await db.commit()
                return
            except Exception as agent_error:
                logger.error(f"Agent execution failed for {content_type}: {agent_error}")
                generation = (await db.execute(select(Model).where(Model.id == generation_id))).scalar_one_or_none()
                if generation:
                    generation.status = "failed"
                    generation.error = f"Agent执行失败: {str(agent_error)[:200]}"
                    await db.commit()
                return

            if not content_data:
                raise Exception(f"生成的{content_type}内容为空")

            title = content_data.get("title", f"{node_name} - {content_type}")

            generation = (await db.execute(select(Model).where(Model.id == generation_id))).scalar_one_or_none()
            if generation:
                data_field = data_field_map[content_type]
                setattr(generation, data_field, content_data)
                generation.status = "ready"
                generation.title = title

                try:
                    file_path = await save_content_as_html(
                        content_data=content_data,
                        content_type=content_type,
                        task_id=task_id,
                        title=title,
                    )
                    generation.file_path = file_path
                except Exception as save_error:
                    logger.error(f"Failed to save {content_type} HTML file: {save_error}")

                await db.commit()
                logger.info(f"{content_type} generation completed for generation {generation_id}")
        except Exception as e:
            logger.error(f"{content_type} generation failed for generation {generation_id}: {e}")
            generation = (await db.execute(select(Model).where(Model.id == generation_id))).scalar_one_or_none()
            if generation:
                generation.status = "failed"
                generation.error = str(e)[:500]
                await db.commit()


@router.post("/{task_id}/video/generate", status_code=202)
async def generate_video(task_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start video script generation asynchronously."""
    from app.models.learning_task import VideoGeneration

    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, "关联的知识节点不存在")

    source_content = ""
    source = (await db.execute(select(Source).where(Source.id == node.source_id))).scalar_one_or_none()
    if source and source.content_text:
        source_content = source.content_text

    generation = VideoGeneration(
        task_id=task.id,
        title=f"{node.name} - 讲解视频",
        status="generating",
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    background_tasks.add_task(
        _generate_content_background,
        generation_id=generation.id,
        task_id=task.id,
        content_type="video",
        node_name=node.name,
        node_description=node.description or "",
        source_content=source_content,
        current_stage=task.current_stage,
        difficulty=task.difficulty,
    )

    return {"generation_id": generation.id, "status": "generating", "message": "视频脚本正在生成中，请查询状态接口获取结果"}


@router.post("/{task_id}/animation/generate", status_code=202)
async def generate_animation(task_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start animation concept generation asynchronously."""
    from app.models.learning_task import AnimationGeneration

    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, "关联的知识节点不存在")

    source_content = ""
    source = (await db.execute(select(Source).where(Source.id == node.source_id))).scalar_one_or_none()
    if source and source.content_text:
        source_content = source.content_text

    generation = AnimationGeneration(
        task_id=task.id,
        title=f"{node.name} - 动画演示",
        status="generating",
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    background_tasks.add_task(
        _generate_content_background,
        generation_id=generation.id,
        task_id=task.id,
        content_type="animation",
        node_name=node.name,
        node_description=node.description or "",
        source_content=source_content,
        current_stage=task.current_stage,
        difficulty=task.difficulty,
    )

    return {"generation_id": generation.id, "status": "generating", "message": "动画演示正在生成中，请查询状态接口获取结果"}


@router.post("/{task_id}/podcast/generate", status_code=202)
async def generate_podcast(task_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start podcast script generation asynchronously."""
    from app.models.learning_task import PodcastGeneration

    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, "关联的知识节点不存在")

    source_content = ""
    source = (await db.execute(select(Source).where(Source.id == node.source_id))).scalar_one_or_none()
    if source and source.content_text:
        source_content = source.content_text

    generation = PodcastGeneration(
        task_id=task.id,
        title=f"{node.name} - 音频播客",
        status="generating",
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    background_tasks.add_task(
        _generate_content_background,
        generation_id=generation.id,
        task_id=task.id,
        content_type="podcast",
        node_name=node.name,
        node_description=node.description or "",
        source_content=source_content,
        current_stage=task.current_stage,
        difficulty=task.difficulty,
    )

    return {"generation_id": generation.id, "status": "generating", "message": "音频播客正在生成中，请查询状态接口获取结果"}


@router.post("/{task_id}/mindmap/generate", status_code=202)
async def generate_mindmap(task_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start mindmap generation asynchronously."""
    from app.models.learning_task import MindmapGeneration

    task = (await db.execute(select(LearningTask).where(LearningTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "学习任务不存在")

    node = (await db.execute(select(GraphNode).where(GraphNode.id == task.node_id))).scalar_one_or_none()
    if not node:
        raise HTTPException(404, "关联的知识节点不存在")

    source_content = ""
    source = (await db.execute(select(Source).where(Source.id == node.source_id))).scalar_one_or_none()
    if source and source.content_text:
        source_content = source.content_text

    generation = MindmapGeneration(
        task_id=task.id,
        title=f"{node.name} - 思维导图",
        status="generating",
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    background_tasks.add_task(
        _generate_content_background,
        generation_id=generation.id,
        task_id=task.id,
        content_type="mindmap",
        node_name=node.name,
        node_description=node.description or "",
        source_content=source_content,
        current_stage=task.current_stage,
        difficulty=task.difficulty,
    )

    return {"generation_id": generation.id, "status": "generating", "message": "思维导图正在生成中，请查询状态接口获取结果"}


# Status and list endpoints
@router.get("/{task_id}/video/status")
async def get_video_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of the latest video generation."""
    from app.models.learning_task import VideoGeneration

    generation = (
        await db.execute(
            select(VideoGeneration)
            .where(VideoGeneration.task_id == task_id)
            .order_by(VideoGeneration.created_at.desc())
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "没有找到视频生成记录")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "script": generation.script if generation.status == "ready" else None,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/animation/status")
async def get_animation_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of the latest animation generation."""
    from app.models.learning_task import AnimationGeneration

    generation = (
        await db.execute(
            select(AnimationGeneration)
            .where(AnimationGeneration.task_id == task_id)
            .order_by(AnimationGeneration.created_at.desc())
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "没有找到动画生成记录")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "concept": generation.concept if generation.status == "ready" else None,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/podcast/status")
async def get_podcast_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of the latest podcast generation."""
    from app.models.learning_task import PodcastGeneration

    generation = (
        await db.execute(
            select(PodcastGeneration)
            .where(PodcastGeneration.task_id == task_id)
            .order_by(PodcastGeneration.created_at.desc())
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "没有找到播客生成记录")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "script": generation.script if generation.status == "ready" else None,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/mindmap/status")
async def get_mindmap_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of the latest mindmap generation."""
    from app.models.learning_task import MindmapGeneration

    generation = (
        await db.execute(
            select(MindmapGeneration)
            .where(MindmapGeneration.task_id == task_id)
            .order_by(MindmapGeneration.created_at.desc())
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "没有找到思维导图生成记录")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "nodes": generation.nodes if generation.status == "ready" else None,
        "edges": generation.edges if generation.status == "ready" else None,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


# List and detail endpoints
@router.get("/{task_id}/video")
async def list_video(task_id: int, db: AsyncSession = Depends(get_db)):
    """List all video generations for a task."""
    from app.models.learning_task import VideoGeneration

    generations = (
        await db.execute(
            select(VideoGeneration)
            .where(VideoGeneration.task_id == task_id)
            .order_by(VideoGeneration.created_at.desc())
        )
    ).scalars().all()

    return [{
        "id": g.id,
        "task_id": g.task_id,
        "title": g.title,
        "status": g.status,
        "file_path": g.file_path,
        "error": g.error,
        "created_at": g.created_at,
    } for g in generations]


@router.get("/{task_id}/animation")
async def list_animation(task_id: int, db: AsyncSession = Depends(get_db)):
    """List all animation generations for a task."""
    from app.models.learning_task import AnimationGeneration

    generations = (
        await db.execute(
            select(AnimationGeneration)
            .where(AnimationGeneration.task_id == task_id)
            .order_by(AnimationGeneration.created_at.desc())
        )
    ).scalars().all()

    return [{
        "id": g.id,
        "task_id": g.task_id,
        "title": g.title,
        "status": g.status,
        "file_path": g.file_path,
        "error": g.error,
        "created_at": g.created_at,
    } for g in generations]


@router.get("/{task_id}/podcast")
async def list_podcast(task_id: int, db: AsyncSession = Depends(get_db)):
    """List all podcast generations for a task."""
    from app.models.learning_task import PodcastGeneration

    generations = (
        await db.execute(
            select(PodcastGeneration)
            .where(PodcastGeneration.task_id == task_id)
            .order_by(PodcastGeneration.created_at.desc())
        )
    ).scalars().all()

    return [{
        "id": g.id,
        "task_id": g.task_id,
        "title": g.title,
        "status": g.status,
        "file_path": g.file_path,
        "error": g.error,
        "created_at": g.created_at,
    } for g in generations]


@router.get("/{task_id}/mindmap")
async def list_mindmap(task_id: int, db: AsyncSession = Depends(get_db)):
    """List all mindmap generations for a task."""
    from app.models.learning_task import MindmapGeneration

    generations = (
        await db.execute(
            select(MindmapGeneration)
            .where(MindmapGeneration.task_id == task_id)
            .order_by(MindmapGeneration.created_at.desc())
        )
    ).scalars().all()

    return [{
        "id": g.id,
        "task_id": g.task_id,
        "title": g.title,
        "status": g.status,
        "file_path": g.file_path,
        "error": g.error,
        "created_at": g.created_at,
    } for g in generations]


# Detail and download endpoints
@router.get("/{task_id}/video/{generation_id}")
async def get_video_detail(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Get video generation detail by ID."""
    from app.models.learning_task import VideoGeneration

    generation = (
        await db.execute(
            select(VideoGeneration).where(VideoGeneration.id == generation_id, VideoGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "视频不存在")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "script": generation.script,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/animation/{generation_id}")
async def get_animation_detail(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Get animation generation detail by ID."""
    from app.models.learning_task import AnimationGeneration

    generation = (
        await db.execute(
            select(AnimationGeneration).where(AnimationGeneration.id == generation_id, AnimationGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "动画不存在")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "concept": generation.concept,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/podcast/{generation_id}")
async def get_podcast_detail(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Get podcast generation detail by ID."""
    from app.models.learning_task import PodcastGeneration

    generation = (
        await db.execute(
            select(PodcastGeneration).where(PodcastGeneration.id == generation_id, PodcastGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "播客不存在")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "script": generation.script,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/mindmap/{generation_id}")
async def get_mindmap_detail(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Get mindmap generation detail by ID."""
    from app.models.learning_task import MindmapGeneration

    generation = (
        await db.execute(
            select(MindmapGeneration).where(MindmapGeneration.id == generation_id, MindmapGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "思维导图不存在")

    return {
        "id": generation.id,
        "task_id": generation.task_id,
        "title": generation.title,
        "status": generation.status,
        "nodes": generation.nodes,
        "edges": generation.edges,
        "file_path": generation.file_path,
        "error": generation.error,
        "created_at": generation.created_at,
    }


@router.get("/{task_id}/video/{generation_id}/download")
async def download_video(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Download video HTML file."""
    from fastapi.responses import FileResponse
    import os
    from app.models.learning_task import VideoGeneration

    generation = (
        await db.execute(
            select(VideoGeneration).where(VideoGeneration.id == generation_id, VideoGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "视频不存在")

    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(404, "视频文件不存在")

    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in generation.title)
    filename = f"{safe_title}.html"

    return FileResponse(
        path=generation.file_path,
        filename=filename,
        media_type="text/html",
    )


@router.get("/{task_id}/animation/{generation_id}/download")
async def download_animation(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Download animation HTML file."""
    from fastapi.responses import FileResponse
    import os
    from app.models.learning_task import AnimationGeneration

    generation = (
        await db.execute(
            select(AnimationGeneration).where(AnimationGeneration.id == generation_id, AnimationGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "动画不存在")

    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(404, "动画文件不存在")

    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in generation.title)
    filename = f"{safe_title}.html"

    return FileResponse(
        path=generation.file_path,
        filename=filename,
        media_type="text/html",
    )


@router.get("/{task_id}/podcast/{generation_id}/download")
async def download_podcast(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Download podcast HTML file."""
    from fastapi.responses import FileResponse
    import os
    from app.models.learning_task import PodcastGeneration

    generation = (
        await db.execute(
            select(PodcastGeneration).where(PodcastGeneration.id == generation_id, PodcastGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "播客不存在")

    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(404, "播客文件不存在")

    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in generation.title)
    filename = f"{safe_title}.html"

    return FileResponse(
        path=generation.file_path,
        filename=filename,
        media_type="text/html",
    )


@router.get("/{task_id}/mindmap/{generation_id}/download")
async def download_mindmap(task_id: int, generation_id: int, db: AsyncSession = Depends(get_db)):
    """Download mindmap HTML file."""
    from fastapi.responses import FileResponse
    import os
    from app.models.learning_task import MindmapGeneration

    generation = (
        await db.execute(
            select(MindmapGeneration).where(MindmapGeneration.id == generation_id, MindmapGeneration.task_id == task_id)
        )
    ).scalar_one_or_none()

    if not generation:
        raise HTTPException(404, "思维导图不存在")

    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(404, "思维导图文件不存在")

    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in generation.title)
    filename = f"{safe_title}.html"

    return FileResponse(
        path=generation.file_path,
        filename=filename,
        media_type="text/html",
    )
