"""Content Generation Services.

Generates HTML files for various content types (video, animation, podcast, mindmap).
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


def _generate_video_html(video_data: dict) -> str:
    """Generate HTML page for video script."""
    title = video_data.get("title", "讲解视频")
    duration = video_data.get("duration_minutes", 15)
    target_audience = video_data.get("target_audience", "")
    learning_objectives = video_data.get("learning_objectives", [])
    scenes = video_data.get("scenes", [])
    summary_scene = video_data.get("summary_scene", {})

    scenes_html = ""
    for scene in scenes:
        scene_id = scene.get("scene_id", 0)
        scene_title = scene.get("title", "")
        scene_duration = scene.get("duration_seconds", 0)
        visual = scene.get("visual", "")
        narration = scene.get("narration", "")
        on_screen_text = scene.get("on_screen_text", "")
        b_roll = scene.get("broll", "")

        scenes_html += f"""
            <div class="scene-card glass rounded-xl p-6 mb-4">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <span class="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 to-pink-500 flex items-center justify-center text-white font-bold">
                            {scene_id}
                        </span>
                        <h3 class="text-xl font-semibold text-white">{scene_title}</h3>
                    </div>
                    <span class="text-sm text-slate-400 bg-white/5 px-3 py-1 rounded-full">
                        时长：{scene_duration}秒
                    </span>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <span class="text-sm font-medium text-blue-400">视觉画面</span>
                        </div>
                        <p class="text-slate-300">{visual}</p>
                    </div>
                    
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                            <span class="text-sm font-medium text-purple-400">旁白文本</span>
                        </div>
                        <p class="text-slate-300 leading-relaxed">{narration}</p>
                    </div>
                    
                    {f'''
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                            </svg>
                            <span class="text-sm font-medium text-yellow-400">屏幕文字</span>
                        </div>
                        <p class="text-slate-300">{on_screen_text}</p>
                    </div>
                    ''' if on_screen_text else ''}
                    
                    {f'''
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h3.586l-1.586-1.586a2 2 0 01-2.828 0L10 6m-9 2h14.586l-1.586-1.586a2 2 0 01-2.828 0L14 2" />
                            </svg>
                            <span class="text-sm font-medium text-green-400">B-roll 画面</span>
                        </div>
                        <p class="text-slate-300">{b_roll}</p>
                    </div>
                    ''' if b_roll else ''}
                </div>
            </div>
        """

    objectives_html = ""
    if learning_objectives:
        objectives_html = "".join([
            f'<li class="flex items-start gap-2"><span class="text-blue-400 mt-1">●</span><span class="text-slate-300">{obj}</span></li>'
            for obj in learning_objectives
        ])

    summary_html = ""
    if summary_scene:
        key_points = summary_scene.get("key_points", [])
        if key_points:
            points_html = "".join([
                f'<li class="flex items-start gap-2"><span class="text-green-400 mt-1">✓</span><span class="text-slate-300">{kp}</span></li>'
                for kp in key_points
            ])
            summary_html = f"""
                <div class="glass rounded-xl p-6 mt-6">
                    <h3 class="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                        <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        总结要点
                    </h3>
                    <ul class="space-y-2">{points_html}</ul>
                    {f'<p class="mt-4 text-yellow-400"><strong>下一步：</strong>{summary_scene.get("next_steps", "")}</p>' if summary_scene.get("next_steps") else ''}
                </div>
            """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.6;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ef4444 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}
        .meta-info {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #94a3b8;
            font-size: 0.875rem;
        }}
        .objectives {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .objectives h3 {{
            color: #60a5fa;
            margin-bottom: 1rem;
            font-size: 1.125rem;
        }}
        .timeline {{
            position: relative;
            padding-left: 2rem;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 0.5rem;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(180deg, #ef4444, #ec4899);
        }}
        .print-btn {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #ef4444, #ec4899);
            color: white;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }}
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ background: white; color: #1e293b; }}
            .glass {{ background: white; border: 1px solid #e2e8f0; }}
            .scene-card {{ border: 1px solid #e2e8f0 !important; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
        </svg>
        打印脚本
    </button>
    
    <div class="container">
        <div class="header glass">
            <h1>{title}</h1>
            <p class="text-slate-400 mt-2">{target_audience}</p>
            <div class="meta-info">
                <div class="meta-item">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    预计时长：{duration} 分钟
                </div>
                <div class="meta-item">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    {len(scenes)} 个场景
                </div>
            </div>
        </div>
        
        {f'''
        <div class="objectives glass">
            <h3 class="flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                学习目标
            </h3>
            <ul class="space-y-2">{objectives_html}</ul>
        </div>
        ''' if objectives_html else ''}
        
        <h2 class="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <svg class="w-7 h-7 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            分镜脚本
        </h2>
        
        <div class="timeline">
            {scenes_html}
        </div>
        
        {summary_html}
        
        <div class="text-center text-slate-500 text-sm mt-8 pb-8">
            生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>
    </div>
</body>
</html>
"""


def _generate_animation_html(animation_data: dict) -> str:
    """Generate HTML page for animation concept."""
    title = animation_data.get("title", "动画演示")
    animation_type = animation_data.get("animation_type", "principle_demo")
    duration = animation_data.get("duration_minutes", 5)
    target_audience = animation_data.get("target_audience", "")
    core_concept = animation_data.get("core_concept", "")
    visual_style = animation_data.get("visual_style", {})
    timeline = animation_data.get("timeline", [])
    key_frames = animation_data.get("key_frames", [])

    timeline_html = ""
    for item in timeline:
        time_start = item.get("time_start", 0)
        time_end = item.get("time_end", 0)
        scene_name = item.get("scene_name", "")
        description = item.get("description", "")
        animations = item.get("animations", [])
        voiceover = item.get("voiceover", "")
        on_screen_text = item.get("on_screen_text", [])

        animations_html = ""
        if animations:
            anim_list = "".join([
                f'<li class="text-slate-300 text-sm"><span class="text-cyan-400 font-mono">[{anim.get("duration", 0)}s]</span> {anim.get("element", "")}: {anim.get("description", "")} <span class="text-purple-400">({anim.get("action", "")})</span></li>'
                for anim in animations
            ])
            animations_html = f"""
                <div class="mt-3 pt-3 border-t border-white/10">
                    <div class="flex items-center gap-2 mb-2">
                        <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span class="text-sm font-medium text-cyan-400">动画效果</span>
                    </div>
                    <ul class="space-y-1 pl-4">{anim_list}</ul>
                </div>
            """

        screen_text_html = ""
        if on_screen_text:
            text_list = "".join([
                f'<span class="inline-block bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded text-sm mr-2 mb-1">{text}</span>'
                for text in on_screen_text
            ])
            screen_text_html = f"""
                <div class="mt-3 pt-3 border-t border-white/10">
                    <div class="flex items-center gap-2 mb-2">
                        <svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                        </svg>
                        <span class="text-sm font-medium text-yellow-400">屏幕文字</span>
                    </div>
                    <div class="flex flex-wrap">{text_list}</div>
                </div>
            """

        timeline_html += f"""
            <div class="relative pl-8 pb-8 border-l-2 border-cyan-500/30 last:border-l-0">
                <div class="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-gradient-to-br from-cyan-400 to-purple-500"></div>
                <div class="glass rounded-xl p-5 hover:bg-white/10 transition-all">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-lg font-semibold text-white">{scene_name}</h3>
                        <span class="text-sm text-cyan-400 font-mono bg-cyan-500/10 px-2 py-1 rounded">
                            {time_start}s - {time_end}s
                        </span>
                    </div>
                    <p class="text-slate-300 mb-3">{description}</p>
                    
                    <div class="bg-slate-800/50 rounded-lg p-3">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                            <span class="text-sm font-medium text-purple-400">配音文本</span>
                        </div>
                        <p class="text-slate-400 text-sm italic">{voiceover}</p>
                    </div>
                    
                    {animations_html}
                    {screen_text_html}
                </div>
            </div>
        """

    key_frames_html = ""
    if key_frames:
        frames_html = "".join([
            f'''
            <div class="glass rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-white">{frame.get("description", "")}</span>
                    <span class="text-sm text-cyan-400 font-mono">{frame.get("time", 0)}s</span>
                </div>
                <div class="flex flex-wrap gap-1">
                    {"".join([f'<span class="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">{elem}</span>' for elem in frame.get("visual_elements", [])])}
                </div>
            </div>
            '''
            for frame in key_frames
        ])
        key_frames_html = f"""
            <div class="mt-8">
                <h3 class="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    关键帧
                </h3>
                <div class="grid grid-cols-2 gap-4">{frames_html}</div>
            </div>
        """

    color_scheme = visual_style.get("color_scheme", [])
    colors_html = "".join([
        f'<div class="flex items-center gap-2"><div class="w-6 h-6 rounded" style="background: {color};"></div><span class="text-sm text-slate-400">{color}</span></div>'
        for color in color_scheme
    ])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.6;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
            border: 1px solid rgba(139, 92, 246, 0.2);
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}
        .core-concept {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .print-btn {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #8b5cf6, #06b6d4);
            color: white;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }}
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ background: white; color: #1e293b; }}
            .glass {{ background: white; border: 1px solid #e2e8f0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
        </svg>
        打印文档
    </button>
    
    <div class="container">
        <div class="header glass">
            <h1>{title}</h1>
            <p class="text-slate-400 mt-2">{target_audience}</p>
            <div class="flex justify-center gap-8 mt-4">
                <div class="text-center">
                    <div class="text-2xl font-bold text-purple-400">{duration}分钟</div>
                    <div class="text-xs text-slate-500">预计时长</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-cyan-400">{len(timeline)}</div>
                    <div class="text-xs text-slate-500">时间片段</div>
                </div>
                <div class="text-center">
                    <div class="text-sm font-medium text-pink-400 px-3 py-1 rounded-full bg-pink-500/10">{animation_type}</div>
                    <div class="text-xs text-slate-500">动画类型</div>
                </div>
            </div>
        </div>
        
        <div class="core-concept glass">
            <h3 class="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                核心概念
            </h3>
            <p class="text-slate-300">{core_concept}</p>
            
            <div class="flex items-center gap-6 mt-4 pt-4 border-t border-white/10">
                <div class="flex items-center gap-2">
                    <span class="text-sm text-slate-400">配色方案：</span>
                    <div class="flex gap-1">{colors_html}</div>
                </div>
                <div class="text-sm text-slate-400">
                    风格：<span class="text-purple-400">{visual_style.get("animation_style", "")}</span>
                </div>
                <div class="text-sm text-slate-400">
                    复杂度：<span class="text-cyan-400">{visual_style.get("complexity_level", "")}</span>
                </div>
            </div>
        </div>
        
        <h2 class="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <svg class="w-7 h-7 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            时间轴
        </h2>
        
        {timeline_html}
        {key_frames_html}
        
        <div class="text-center text-slate-500 text-sm mt-8 pb-8">
            生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>
    </div>
</body>
</html>
"""


def _generate_podcast_html(podcast_data: dict) -> str:
    """Generate HTML page for podcast script."""
    title = podcast_data.get("title", "音频播客")
    subtitle = podcast_data.get("subtitle", "")
    duration = podcast_data.get("duration_minutes", 20)
    target_audience = podcast_data.get("target_audience", "")
    episode_summary = podcast_data.get("episode_summary", "")
    host = podcast_data.get("host", {})
    segments = podcast_data.get("segments", [])
    key_takeaways = podcast_data.get("key_takeaways", [])
    resources = podcast_data.get("resources", [])
    next_episode_teaser = podcast_data.get("next_episode_teaser", "")

    segments_html = ""
    for segment in segments:
        segment_id = segment.get("segment_id", 0)
        seg_title = segment.get("title", "")
        seg_duration = segment.get("duration_seconds", 0)
        seg_type = segment.get("type", "")
        transcript = segment.get("transcript", "")
        speaker_notes = segment.get("speaker_notes", "")
        sound_effects = segment.get("sound_effects", [])
        background_music = segment.get("background_music", "")

        type_colors = {
            "intro": "text-green-400 bg-green-500/10",
            "concept": "text-blue-400 bg-blue-500/10",
            "example": "text-yellow-400 bg-yellow-500/10",
            "qna": "text-purple-400 bg-purple-500/10",
            "summary": "text-cyan-400 bg-cyan-500/10",
            "outro": "text-pink-400 bg-pink-500/10",
        }
        type_class = type_colors.get(seg_type, "text-slate-400 bg-slate-500/10")

        sound_effects_html = ""
        if sound_effects:
            effects = "".join([
                f'<span class="inline-block bg-orange-500/20 text-orange-300 px-2 py-1 rounded text-sm mr-2 mb-1">🔊 {effect}</span>'
                for effect in sound_effects
            ])
            sound_effects_html = f"""
                <div class="mt-3 pt-3 border-t border-white/10">
                    <div class="flex items-center gap-2 mb-2">
                        <svg class="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                        </svg>
                        <span class="text-sm font-medium text-orange-400">音效</span>
                    </div>
                    <div class="flex flex-wrap">{effects}</div>
                </div>
            """

        segments_html += f"""
            <div class="glass rounded-xl p-6 mb-4 transition-all hover:bg-white/10">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white font-bold text-sm">
                            {segment_id}
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-white">{seg_title}</h3>
                            <span class="text-xs px-2 py-0.5 rounded-full {type_class}">{seg_type}</span>
                        </div>
                    </div>
                    <span class="text-sm text-slate-400">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {seg_duration}秒
                    </span>
                </div>
                
                <div class="bg-slate-800/50 rounded-lg p-4 mb-3">
                    <div class="flex items-center gap-2 mb-2">
                        <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <span class="text-sm font-medium text-emerald-400">对话文稿</span>
                    </div>
                    <p class="text-slate-300 leading-relaxed whitespace-pre-line">{transcript}</p>
                </div>
                
                {f'''
                <div class="flex items-start gap-2 text-sm text-purple-300 bg-purple-500/10 p-3 rounded-lg">
                    <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span class="italic">{speaker_notes}</span>
                </div>
                ''' if speaker_notes else ''}
                
                {sound_effects_html}
                
                {f'''
                <div class="mt-3 pt-3 border-t border-white/10">
                    <div class="flex items-center gap-2">
                        <svg class="w-4 h-4 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                        </svg>
                        <span class="text-sm font-medium text-pink-400">背景音乐：</span>
                        <span class="text-sm text-slate-400">{background_music}</span>
                    </div>
                </div>
                ''' if background_music else ''}
            </div>
        """

    takeaways_html = ""
    if key_takeaways:
        takeaways_html = "".join([
            f'<li class="flex items-start gap-2"><span class="text-emerald-400 mt-1">🎯</span><span class="text-slate-300">{kp}</span></li>'
            for kp in key_takeaways
        ])

    resources_html = ""
    if resources:
        resources_html = "".join([
            f'<li class="flex items-start gap-2"><span class="text-blue-400 mt-1">📚</span><span class="text-slate-300">{res}</span></li>'
            for res in resources
        ])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #064e3b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.6;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(34, 197, 94, 0.1) 100%);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #10b981 0%, #22c55e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        .host-card {{
            display: inline-flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 1.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 0.75rem;
            margin-top: 1.5rem;
        }}
        .host-avatar {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #10b981, #06b6d4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: bold;
        }}
        .summary-box {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .takeaways-box {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        .print-btn {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #10b981, #22c55e);
            color: white;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }}
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ background: white; color: #1e293b; }}
            .glass {{ background: white; border: 1px solid #e2e8f0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
        </svg>
        打印脚本
    </button>
    
    <div class="container">
        <div class="header glass">
            <h1>{title}</h1>
            <p class="text-slate-400 text-lg">{subtitle}</p>
            <div class="flex justify-center gap-8 mt-4">
                <div class="text-center">
                    <div class="text-2xl font-bold text-emerald-400">{duration}分钟</div>
                    <div class="text-xs text-slate-500">节目时长</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-400">{len(segments)}</div>
                    <div class="text-xs text-slate-500">段落数量</div>
                </div>
            </div>
            <div class="host-card">
                <div class="host-avatar">{host.get("name", "主播")[0] if host.get("name") else "主"}</div>
                <div class="text-left">
                    <div class="font-medium text-white">{host.get("name", "主播")}</div>
                    <div class="text-xs text-slate-400">{host.get("persona", "")}</div>
                </div>
            </div>
        </div>
        
        <div class="summary-box glass">
            <h3 class="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                本期简介
            </h3>
            <p class="text-slate-300">{episode_summary}</p>
            <p class="text-sm text-slate-400 mt-2">{target_audience}</p>
        </div>
        
        <h2 class="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <svg class="w-7 h-7 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            节目脚本
        </h2>
        
        {segments_html}
        
        {f'''
        <div class="takeaways-box glass">
            <h3 class="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                核心要点
            </h3>
            <ul class="space-y-2">{takeaways_html}</ul>
        </div>
        ''' if takeaways_html else ''}
        
        {f'''
        <div class="glass rounded-xl p-6 mt-4">
            <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                推荐资源
            </h3>
            <ul class="space-y-2">{resources_html}</ul>
        </div>
        ''' if resources_html else ''}
        
        {f'''
        <div class="glass rounded-xl p-6 mt-4 text-center">
            <p class="text-sm text-slate-400 mb-2">下一期预告</p>
            <p class="text-lg text-cyan-400 font-medium">{next_episode_teaser}</p>
        </div>
        ''' if next_episode_teaser else ''}
        
        <div class="text-center text-slate-500 text-sm mt-8 pb-8">
            生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>
    </div>
</body>
</html>
"""


def _generate_mindmap_html(mindmap_data: dict) -> str:
    """Generate HTML page for mind map."""
    title = mindmap_data.get("title", "思维导图")
    root_node = mindmap_data.get("root_node", {})
    nodes = mindmap_data.get("nodes", [])
    edges = mindmap_data.get("edges", [])
    layout_config = mindmap_data.get("layout_config", {})
    legend = mindmap_data.get("legend", {})

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)

    colors_legend = legend.get("colors", {})
    colors_html = ""
    for color_hex, label in colors_legend.items():
        colors_html += f'''
            <div class="flex items-center gap-2">
                <div class="w-4 h-4 rounded" style="background: {color_hex};"></div>
                <span class="text-sm text-slate-400">{label}</span>
            </div>
        '''

    icons_legend = legend.get("icons", {})
    icons_html = ""
    for icon_name, label in icons_legend.items():
        icons_html += f'<span class="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">{icon_name}: {label}</span>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.6;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
            border: 1px solid rgba(59, 130, 246, 0.2);
        }}
        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        .mindmap-container {{
            width: 100%;
            height: 600px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
            position: relative;
        }}
        .controls {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.5rem;
            z-index: 10;
        }}
        .control-btn {{
            width: 36px;
            height: 36px;
            border-radius: 0.5rem;
            border: none;
            background: rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}
        .control-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        .legend {{
            margin-top: 1.5rem;
            padding: 1.5rem;
            border-radius: 0.75rem;
        }}
        .nodes-list {{
            margin-top: 1.5rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        .node-item {{
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 0.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-left: 3px solid #3b82f6;
        }}
        .print-btn {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #3b82f6, #06b6d4);
            color: white;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
            z-index: 100;
        }}
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }}
        @media print {{
            .print-btn, .controls {{ display: none; }}
            body {{ background: white; color: #1e293b; }}
            .glass {{ background: white; border: 1px solid #e2e8f0; }}
            .mindmap-container {{ background: #f8fafc; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
        </svg>
        打印文档
    </button>
    
    <div class="container">
        <div class="header glass">
            <h1>{title}</h1>
            <p class="text-slate-400 mt-2">{root_node.get('label', '')}</p>
            <p class="text-sm text-slate-500 mt-1">{root_node.get('description', '')}</p>
            <div class="flex justify-center gap-8 mt-4">
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-400">{len(nodes)}</div>
                    <div class="text-xs text-slate-500">节点</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-cyan-400">{len(edges)}</div>
                    <div class="text-xs text-slate-500">关联</div>
                </div>
            </div>
        </div>
        
        <div class="mindmap-container glass">
            <div class="controls">
                <button class="control-btn" onclick="zoomIn()">+</button>
                <button class="control-btn" onclick="zoomOut()">-</button>
                <button class="control-btn" onclick="resetView()">⟲</button>
            </div>
            <div id="mindmap" style="width: 100%; height: 100%; overflow: auto; padding: 2rem;"></div>
        </div>
        
        {f'''
        <div class="legend glass">
            <h3 class="text-lg font-semibold text-white mb-4">图例</h3>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="text-sm font-medium text-slate-300 mb-2">颜色</h4>
                    {colors_html}
                </div>
                <div>
                    <h4 class="text-sm font-medium text-slate-300 mb-2">图标</h4>
                    <div class="flex flex-wrap gap-2">{icons_html}</div>
                </div>
            </div>
        </div>
        ''' if colors_html or icons_html else ''}
        
        <div class="nodes-list">
            <h3 class="text-lg font-semibold text-white mb-4">节点列表</h3>
            {"".join([f'''
            <div class="node-item">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-3 h-3 rounded-full" style="background: {node.get("color", "#3b82f6")};"></div>
                    <span class="font-medium text-white">{node.get("label", "")}</span>
                    <span class="text-xs text-slate-500">[{node.get("importance", "medium")}]</span>
                </div>
                <p class="text-sm text-slate-400 ml-5">{node.get("description", "")}</p>
            </div>
            ''' for node in nodes])}
        </div>
        
        <div class="text-center text-slate-500 text-sm mt-8 pb-8">
            生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>
    </div>
    
    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        let scale = 1;
        
        function renderMindmap() {{
            const container = document.getElementById('mindmap');
            const rootNode = nodes.find(n => n.parent_id === 'root' || !n.parent_id);
            
            if (!rootNode && nodes.length > 0) {{
                // Build hierarchical structure
                const nodeMap = {{}};
                nodes.forEach(n => {{ nodeMap[n.id] = {{...n, children: []}}; }});
                
                // Build tree
                const roots = [];
                nodes.forEach(n => {{
                    const node = nodeMap[n.id];
                    if (n.parent_id && nodeMap[n.parent_id]) {{
                        nodeMap[n.parent_id].children.push(node);
                    }} else {{
                        roots.push(node);
                    }}
                }});
                
                container.innerHTML = renderTree(roots.length > 0 ? roots[0] : nodes[0]);
            }} else if (nodes.length > 0) {{
                container.innerHTML = renderTree(nodes[0]);
            }}
        }}
        
        function renderTree(node, level = 0) {{
            const color = node.color || '#3b82f6';
            const marginLeft = level * 40;
            const marginBottom = 20;
            
            let childrenHtml = '';
            if (node.children && node.children.length > 0) {{
                childrenHtml = node.children.map(child => renderTree(child, level + 1)).join('');
            }}
            
            return `
                <div style="margin-left: ${{marginLeft}}px; margin-bottom: ${{marginBottom}}px;">
                    <div style="
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        padding: 0.75rem 1.25rem;
                        background: ${{color}}20;
                        border: 2px solid ${{color}};
                        border-radius: 0.75rem;
                        color: #e2e8f0;
                        font-weight: 500;
                    ">
                        <span>${{node.label || node.id}}</span>
                    </div>
                    ${{childrenHtml}}
                </div>
            `;
        }}
        
        function zoomIn() {{
            scale *= 1.2;
            document.getElementById('mindmap').style.transform = `scale(${{scale}})`;
        }}
        
        function zoomOut() {{
            scale /= 1.2;
            document.getElementById('mindmap').style.transform = `scale(${{scale}})`;
        }}
        
        function resetView() {{
            scale = 1;
            document.getElementById('mindmap').style.transform = `scale(1)`;
        }}
        
        // Initialize
        renderMindmap();
    </script>
</body>
</html>
"""


async def save_content_as_html(content_data: dict, content_type: str, task_id: int, title: str) -> str:
    """Save generated content as HTML file.
    
    Args:
        content_data: Content data dict
        content_type: Type of content ('video', 'animation', 'podcast', 'mindmap')
        task_id: Task ID
        title: Content title
        
    Returns:
        Path to the saved HTML file
    """
    if not content_data:
        raise ValueError("No content data to save")
    
    generators = {
        'video': _generate_video_html,
        'animation': _generate_animation_html,
        'podcast': _generate_podcast_html,
        'mindmap': _generate_mindmap_html,
    }
    
    generator = generators.get(content_type)
    if not generator:
        raise ValueError(f"Unknown content type: {content_type}")
    
    html_content = generator(content_data)
    
    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"task_{task_id}_{content_type}_{safe_title}_{timestamp}.html"
    
    from app.config import settings
    
    if content_type == 'video':
        file_path = settings.video_output_dir / filename
    elif content_type == 'animation':
        file_path = settings.animation_output_dir / filename
    elif content_type == 'podcast':
        file_path = settings.podcast_output_dir / filename
    elif content_type == 'mindmap':
        file_path = settings.mindmap_output_dir / filename
    else:
        file_path = settings.output_dir / filename
    
    try:
        file_path.write_text(html_content, encoding="utf-8")
        logger.info(f"{content_type} saved to: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to save {content_type}: {e}")
        raise