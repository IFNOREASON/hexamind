"""PPT HTML Generator Service.

Generates beautiful HTML presentations from slide data.
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


def _generate_html(slides: list[dict], title: str, theme: dict) -> str:
    """Generate HTML presentation from slides data."""
    
    primary_color = theme.get("primary_color", "#3B82F6")
    secondary_color = theme.get("secondary_color", "#8B5CF6")
    accent_color = theme.get("accent_color", "#F59E0B")
    
    slides_html = ""
    for idx, slide in enumerate(slides):
        slide_type = slide.get("type", "content")
        slide_title = slide.get("title", "")
        slide_layout = slide.get("layout", "single")
        slide_content = slide.get("content", "")
        slide_content_list = slide.get("content_list", [])
        highlights = slide.get("highlights", [])
        key_points = slide.get("key_points", [])
        next_steps = slide.get("next_steps", "")
        subtitle = slide.get("subtitle", "")
        illustration = slide.get("illustration", "")
        notes = slide.get("notes", "")
        
        slide_html = ""
        
        if slide_type == "cover":
            slide_html = f"""
                <section class="slide slide-cover" data-slide="{idx}">
                    <div class="slide-content cover-content">
                        <div class="cover-title">{slide_title}</div>
                        {f'<div class="cover-subtitle">{subtitle}</div>' if subtitle else ''}
                        {f'<div class="cover-illustration">{illustration}</div>' if illustration else ''}
                    </div>
                </section>
            """
        elif slide_type == "summary":
            key_points_html = "".join([
                f'<li class="key-point">{kp}</li>'
                for kp in key_points
            ])
            slide_html = f"""
                <section class="slide slide-summary" data-slide="{idx}">
                    <div class="slide-header">
                        <h2 class="slide-title">{slide_title}</h2>
                    </div>
                    <div class="slide-content">
                        <ul class="summary-list">
                            {key_points_html}
                        </ul>
                        {f'<div class="next-steps"><strong>下一步：</strong>{next_steps}</div>' if next_steps else ''}
                    </div>
                </section>
            """
        elif slide_type == "quote":
            slide_html = f"""
                <section class="slide slide-quote" data-slide="{idx}">
                    <div class="slide-content">
                        <blockquote class="quote-text">"{slide_content or (slide_content_list[0] if slide_content_list else '')}"</blockquote>
                        {f'<div class="quote-notes">{notes}</div>' if notes else ''}
                    </div>
                </section>
            """
        else:
            # Content slide
            if slide_content_list:
                content_html = ""
                for i, item in enumerate(slide_content_list):
                    is_highlight = i in highlights
                    highlight_class = "highlight" if is_highlight else ""
                    bullet_html = f'<span class="bullet" style="color: {accent_color}">●</span>'
                    content_html += f"""
                        <div class="content-item {highlight_class}">
                            {bullet_html}
                            <span>{item}</span>
                        </div>
                    """
            elif slide_content:
                # Split by newlines
                lines = [line.strip() for line in slide_content.split('\n') if line.strip()]
                content_html = ""
                for i, line in enumerate(lines):
                    is_highlight = i in highlights
                    highlight_class = "highlight" if is_highlight else ""
                    bullet_html = f'<span class="bullet" style="color: {accent_color}">●</span>'
                    content_html += f"""
                        <div class="content-item {highlight_class}">
                            {bullet_html}
                            <span>{line}</span>
                        </div>
                    """
            else:
                content_html = '<div class="content-placeholder">暂无内容</div>'
            
            illustration_html = ""
            if illustration:
                illustration_html = f"""
                    <div class="slide-illustration">
                        <div class="illustration-placeholder">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                <polyline points="21 15 16 10 5 21"></polyline>
                            </svg>
                            <span>{illustration}</span>
                        </div>
                    </div>
                """
            
            layout_class = f"layout-{slide_layout.replace('-', '_')}"
            
            slide_html = f"""
                <section class="slide slide-content {layout_class}" data-slide="{idx}">
                    <div class="slide-header">
                        <h2 class="slide-title">{slide_title}</h2>
                    </div>
                    <div class="slide-content">
                        <div class="content-list">
                            {content_html}
                        </div>
                        {illustration_html}
                    </div>
                </section>
            """
        
        slides_html += slide_html
    
    total_slides = len(slides)
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #e2e8f0;
            min-height: 100vh;
            overflow: hidden;
        }}
        
        .presentation {{
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        
        .slides-container {{
            position: relative;
            width: 100%;
            height: 100%;
        }}
        
        .slide {{
            position: absolute;
            width: 100%;
            height: 100%;
            display: none;
            flex-direction: column;
            opacity: 0;
            transition: opacity 0.5s ease;
        }}
        
        .slide.active {{
            display: flex;
            opacity: 1;
        }}
        
        .slide-cover {{
            background: linear-gradient(135deg, {primary_color}20 0%, {secondary_color}20 100%);
            align-items: center;
            justify-content: center;
        }}
        
        .cover-content {{
            text-align: center;
            padding: 4rem;
        }}
        
        .cover-title {{
            font-size: 4rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 1.5rem;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.3);
            background: linear-gradient(135deg, #fff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .cover-subtitle {{
            font-size: 1.5rem;
            color: #94a3b8;
            margin-bottom: 2rem;
        }}
        
        .cover-illustration {{
            font-size: 1rem;
            color: #64748b;
            font-style: italic;
        }}
        
        .slide-header {{
            padding: 2rem 4rem 1rem;
            border-bottom: 3px solid {primary_color};
        }}
        
        .slide-title {{
            font-size: 2.5rem;
            font-weight: 600;
            color: {primary_color};
        }}
        
        .slide-content {{
            flex: 1;
            padding: 2rem 4rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .content-list {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .content-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            font-size: 1.5rem;
            line-height: 1.8;
            color: #cbd5e1;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .content-item:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .content-item.highlight {{
            background: {accent_color}20;
            color: #fff;
            border-left: 4px solid {accent_color};
        }}
        
        .content-item .bullet {{
            flex-shrink: 0;
            margin-top: 0.75rem;
        }}
        
        .slide-illustration {{
            margin-top: 2rem;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            border: 1px dashed {primary_color}40;
        }}
        
        .illustration-placeholder {{
            display: flex;
            align-items: center;
            gap: 1rem;
            color: #64748b;
            font-style: italic;
        }}
        
        .illustration-placeholder svg {{
            width: 32px;
            height: 32px;
            opacity: 0.5;
        }}
        
        .slide-summary .summary-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        
        .slide-summary .key-point {{
            font-size: 1.5rem;
            color: #cbd5e1;
            padding: 1rem 1.5rem;
            background: {primary_color}10;
            border-left: 4px solid {primary_color};
            border-radius: 0 8px 8px 0;
        }}
        
        .slide-summary .next-steps {{
            margin-top: 2rem;
            padding: 1.5rem;
            background: {secondary_color}10;
            border-radius: 12px;
            color: #a5b4fc;
            font-size: 1.25rem;
        }}
        
        .slide-quote {{
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, {secondary_color}10 0%, {primary_color}10 100%);
        }}
        
        .quote-text {{
            font-size: 2.5rem;
            font-style: italic;
            color: #e2e8f0;
            text-align: center;
            max-width: 80%;
            line-height: 1.6;
            position: relative;
            padding: 2rem;
        }}
        
        .quote-text::before,
        .quote-text::after {{
            content: '"';
            font-size: 4rem;
            color: {primary_color}40;
            position: absolute;
        }}
        
        .quote-text::before {{
            top: -1rem;
            left: -1rem;
        }}
        
        .quote-text::after {{
            bottom: -3rem;
            right: -1rem;
        }}
        
        .quote-notes {{
            margin-top: 2rem;
            color: #64748b;
            font-size: 1rem;
        }}
        
        .controls {{
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 2rem;
            padding: 1rem 2rem;
            background: rgba(15, 23, 42, 0.9);
            border-radius: 50px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .control-btn {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: none;
            background: {primary_color};
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}
        
        .control-btn:hover {{
            background: {secondary_color};
            transform: scale(1.1);
        }}
        
        .control-btn:disabled {{
            background: #475569;
            cursor: not-allowed;
            transform: none;
        }}
        
        .slide-counter {{
            font-size: 1.25rem;
            color: #94a3b8;
            min-width: 80px;
            text-align: center;
        }}
        
        .slide-counter .current {{
            color: {primary_color};
            font-weight: 600;
        }}
        
        .navigation-dots {{
            position: fixed;
            right: 2rem;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        
        .nav-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #475569;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .nav-dot:hover {{
            background: #64748b;
        }}
        
        .nav-dot.active {{
            background: {primary_color};
            transform: scale(1.3);
        }}
        
        .presentation-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(to bottom, rgba(15, 23, 42, 0.9), transparent);
            z-index: 100;
        }}
        
        .presentation-title {{
            font-size: 1rem;
            color: #94a3b8;
        }}
        
        .fullscreen-btn {{
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #cbd5e1;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.3s ease;
        }}
        
        .fullscreen-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        .speaker-notes {{
            position: fixed;
            bottom: 6rem;
            left: 2rem;
            right: 2rem;
            max-height: 100px;
            overflow-y: auto;
            padding: 1rem;
            background: rgba(15, 23, 42, 0.95);
            border-radius: 12px;
            border: 1px solid {primary_color}40;
            display: none;
        }}
        
        .speaker-notes.visible {{
            display: block;
        }}
        
        .speaker-notes h4 {{
            color: {primary_color};
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }}
        
        .speaker-notes p {{
            color: #94a3b8;
            font-size: 0.875rem;
            line-height: 1.6;
        }}
        
        .notes-toggle {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 0.5rem 1rem;
            background: {secondary_color};
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.3s ease;
        }}
        
        .notes-toggle:hover {{
            background: {primary_color};
        }}
    </style>
</head>
<body>
    <div class="presentation">
        <div class="presentation-header">
            <div class="presentation-title">{title}</div>
            <button class="fullscreen-btn" onclick="toggleFullscreen()">全屏模式</button>
        </div>
        
        <div class="slides-container">
            {slides_html}
        </div>
        
        <div class="navigation-dots">
            {"".join([f'<div class="nav-dot" data-index="{i}" onclick="goToSlide({i})"></div>' for i in range(total_slides)])}
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="previousSlide()" id="prevBtn">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>
            <div class="slide-counter">
                <span class="current" id="currentSlide">1</span> / <span id="totalSlides">{total_slides}</span>
            </div>
            <button class="control-btn" onclick="nextSlide()" id="nextBtn">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>
        </div>
        
        <button class="notes-toggle" onclick="toggleNotes()">演讲者备注</button>
        
        <div class="speaker-notes" id="speakerNotes">
            <h4>演讲者备注</h4>
            <p id="notesContent"></p>
        </div>
    </div>
    
    <script>
        let currentSlideIndex = 0;
        const totalSlides = {total_slides};
        const slides = document.querySelectorAll('.slide');
        const dots = document.querySelectorAll('.nav-dot');
        
        const notesData = {json.dumps([slide.get('notes', '') for slide in slides])};
        
        function showSlide(index) {{
            if (index < 0 || index >= totalSlides) return;
            
            currentSlideIndex = index;
            
            slides.forEach((slide, i) => {{
                slide.classList.toggle('active', i === index);
            }});
            
            dots.forEach((dot, i) => {{
                dot.classList.toggle('active', i === index);
            }});
            
            document.getElementById('currentSlide').textContent = index + 1;
            document.getElementById('prevBtn').disabled = index === 0;
            document.getElementById('nextBtn').disabled = index === totalSlides - 1;
            
            const notesContent = document.getElementById('notesContent');
            if (notesData[index]) {{
                notesContent.textContent = notesData[index];
            }} else {{
                notesContent.textContent = '暂无备注';
            }}
        }}
        
        function nextSlide() {{
            if (currentSlideIndex < totalSlides - 1) {{
                showSlide(currentSlideIndex + 1);
            }}
        }}
        
        function previousSlide() {{
            if (currentSlideIndex > 0) {{
                showSlide(currentSlideIndex - 1);
            }}
        }}
        
        function goToSlide(index) {{
            showSlide(index);
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        function toggleNotes() {{
            const notes = document.getElementById('speakerNotes');
            notes.classList.toggle('visible');
        }}
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === ' ') {{
                nextSlide();
            }} else if (e.key === 'ArrowLeft') {{
                previousSlide();
            }} else if (e.key === 'f' || e.key === 'F') {{
                toggleFullscreen();
            }} else if (e.key === 'n' || e.key === 'N') {{
                toggleNotes();
            }}
        }});
        
        showSlide(0);
    </script>
</body>
</html>
"""


async def save_ppt_as_html(slides: list[dict], ppt_id: int, title: str, task_id: int) -> str:
    """Save PPT slides as HTML file.
    
    Args:
        slides: List of slide data
        ppt_id: PPT generation ID
        title: PPT title
        task_id: Task ID
        
    Returns:
        Path to the saved HTML file
    """
    if not slides:
        raise ValueError("No slides to save")
    
    theme = slides[0].get("theme", {}) if slides else {}
    
    html_content = _generate_html(slides, title, theme)
    
    safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"task_{task_id}_ppt_{ppt_id}_{safe_title}_{timestamp}.html"
    
    file_path = settings.ppt_output_dir / filename
    
    try:
        file_path.write_text(html_content, encoding="utf-8")
        logger.info(f"PPT saved to: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to save PPT: {e}")
        raise


def generate_file_hash(file_path: str) -> str:
    """Generate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
