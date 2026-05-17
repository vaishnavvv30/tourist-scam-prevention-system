import os
import re

file_path = 'static/css/style.css'
with open(file_path, 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Update Root Variables (Light Theme)
new_root = ''':root {
    --bg-primary: #f8f9fa;
    --bg-secondary: #ffffff;
    --bg-card: #ffffff;
    --bg-glass: #ffffff;
    --bg-glass-hover: #fafafa;
    --border-glass: #e2e8f0;
    --border-glow: #cbd5e1;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --accent-primary: #0f172a;
    --accent-secondary: #334155;
    --accent-gradient: #0f172a;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --info: #3b82f6;
    --critical: #8b5cf6;
    --shadow-glow: none;
    --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.025);
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --transition: all 0.2s ease;
    --transition-bounce: all 0.2s ease;
    
    --doodle-color: #cbd5e1;
    --doodle-opacity: 0.1;
    --doodle-glow: none;
}'''
css = re.sub(r':root\s*\{[^}]+\}', new_root, css, count=1)

# 2. Update Dark Theme Variables
new_dark = '''[data-theme="dark"] {
    --bg-primary: #09090b;
    --bg-secondary: #18181b;
    --bg-card: #18181b;
    --bg-glass: #18181b;
    --bg-glass-hover: #27272a;
    --border-glass: #27272a;
    --border-glow: #3f3f46;
    --text-primary: #fafafa;
    --text-secondary: #a1a1aa;
    --text-muted: #71717a;
    --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.5);
    
    --doodle-color: #27272a;
    --doodle-opacity: 0.2;
    --doodle-glow: none;
    --accent-primary: #fafafa;
    --accent-secondary: #e4e4e7;
    --accent-gradient: #fafafa;
}'''
css = re.sub(r'\[data-theme="dark"\]\s*\{[^}]+\}', new_dark, css, count=1)

# 3. Remove body::before glowing orbs
css = re.sub(r'body::before\s*\{[^\}]+\}', 'body::before { display: none; }', css)
css = re.sub(r'\[data-theme="dark"\] body::before\s*\{[^\}]+\}', '[data-theme="dark"] body::before { display: none; }', css)

# 4. Remove travel Float animations and replace with subtle static or slow movement
css = re.sub(r'@keyframes travelFloat\s*\{[^\}]+\}', '@keyframes travelFloat { 0% { transform: translateY(105vh); opacity: 0; } 10% { opacity: var(--doodle-opacity); } 90% { opacity: var(--doodle-opacity); } 100% { transform: translateY(-10vh); opacity: 0; } }', css)

# 5. Redesign buttons
css = re.sub(r'\.btn-primary-glow\s*\{[^\}]+\}', '.btn-primary-glow { background: var(--accent-primary); border: 1px solid var(--border-glass); color: var(--bg-primary); font-weight: 500; font-size: 0.95rem; padding: 0.6rem 1.2rem; border-radius: var(--radius-sm); transition: var(--transition); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }', css)
css = re.sub(r'\.btn-primary-glow:hover\s*\{[^\}]+\}', '.btn-primary-glow:hover { background: var(--accent-secondary); color: var(--bg-primary); transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }', css)
css = re.sub(r'\.btn-primary-glow::after\s*\{[^\}]+\}', '.btn-primary-glow::after { display: none; }', css)
css = re.sub(r'\.btn-primary-glow:hover::after\s*\{[^\}]+\}', '.btn-primary-glow:hover::after { display: none; }', css)
css = re.sub(r'\.btn-glass\s*\{[^\}]+\}', '.btn-glass { background: var(--bg-card); border: 1px solid var(--border-glass); color: var(--text-primary); font-weight: 500; padding: 0.6rem 1.5rem; border-radius: var(--radius-md); transition: var(--transition); box-shadow: var(--shadow-card); }', css)
css = re.sub(r'\.btn-glass:hover\s*\{[^\}]+\}', '.btn-glass:hover { background: var(--bg-primary); }', css)

# 6. Redesign Glass Cards
css = re.sub(r'\.glass-card\s*\{[^\}]+\}', '.glass-card { background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: 1.5rem; transition: var(--transition); box-shadow: var(--shadow-card); position: relative; z-index: 1; }', css)
css = re.sub(r'\.glass-card:hover\s*\{[^\}]+\}', '.glass-card:hover { border-color: var(--border-glow); }', css)
css = re.sub(r'\.glass-card-static\s*\{[^\}]+\}', '.glass-card-static { background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: 1.5rem; box-shadow: var(--shadow-card); }', css)
css = re.sub(r'\.stat-card\s*\{[^\}]+\}', '.stat-card { background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: 1.5rem; text-align: left; transition: var(--transition); box-shadow: var(--shadow-card); position: relative; overflow: hidden; }', css)
css = re.sub(r'\.stat-card:hover\s*\{[^\}]+\}', '.stat-card:hover { border-color: var(--border-glow); transform: translateY(-2px); }', css)

# 7. Remove glow accents
css = re.sub(r'\.stat-card::before\s*\{[^\}]+\}', '.stat-card::before { display: none; }', css)
css = re.sub(r'\.glass-card::before\s*\{[^\}]+\}', '.glass-card::before { display: none; }', css)
css = re.sub(r'\.glass-card:hover::before\s*\{[^\}]+\}', '.glass-card:hover::before { display: none; }', css)

# 8. Navbar redesign
css = re.sub(r'\.navbar-scamguard\s*\{[^\}]+\}', '.navbar-scamguard { background: var(--bg-secondary) !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border-bottom: 1px solid var(--border-glass); padding: 0.75rem 0; position: sticky; top: 0; z-index: 1050; }', css)
css = re.sub(r'\.navbar-scamguard \.navbar-brand\s*\{[^\}]+\}', '.navbar-scamguard .navbar-brand { font-weight: 600; font-size: 1.25rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem; letter-spacing: -0.02em; }', css)
css = re.sub(r'\[data-theme="dark"\] \.navbar-scamguard\s*\{[^\}]+\}', '[data-theme="dark"] .navbar-scamguard { background: var(--bg-secondary) !important; border-bottom: 1px solid var(--border-glass); box-shadow: 0 1px 2px rgba(0,0,0,0.5); }', css)
css = re.sub(r'\.navbar-scamguard \.navbar-brand \.brand-icon\s*\{[^\}]+\}', '.navbar-scamguard .navbar-brand .brand-icon { font-size: 1.4rem; color: var(--text-primary); }', css)

# 9. Typography Updates (Letter spacing for headings)
css = re.sub(r'h1,\s*h2,\s*h3,\s*h4,\s*h5,\s*h6\s*\{[^\}]+\}', 'h1, h2, h3, h4, h5, h6 { font-weight: 600; color: var(--text-primary); line-height: 1.2; letter-spacing: -0.02em; }', css)

# 10. Fix dark mode cards
css = re.sub(r'\[data-theme="dark"\] \.glass-card,\s*\[data-theme="dark"\] \.glass-card-static,\s*\[data-theme="dark"\] \.stat-card\s*\{[^\}]+\}', '[data-theme="dark"] .glass-card,\n[data-theme="dark"] .glass-card-static,\n[data-theme="dark"] .stat-card { background: var(--bg-card); border-color: var(--border-glass); box-shadow: var(--shadow-card); }', css)
css = re.sub(r'\[data-theme="dark"\] \.glass-card:hover\s*\{[^\}]+\}', '[data-theme="dark"] .glass-card:hover { border-color: var(--border-glow); box-shadow: var(--shadow-card); }', css)

# 11. Remove gradient texts and backgrounds
css = re.sub(r'\.text-gradient\s*\{[^\}]+\}', '.text-gradient { color: var(--text-primary); font-weight: 600; }', css)
css = re.sub(r'\.bg-gradient-scamguard\s*\{[^\}]+\}', '.bg-gradient-scamguard { background: var(--bg-secondary); }', css)

# Fix .stat-value
css = re.sub(r'\.stat-card \.stat-value\s*\{[^\}]+\}', '.stat-card .stat-value { font-size: 1.75rem; font-weight: 600; color: var(--text-primary); letter-spacing: -0.02em; }', css)

# Change badge glass to normal pill
css = re.sub(r'\.badge-glass\s*\{[^\}]+\}', '.badge-glass { background: var(--bg-primary); border: 1px solid var(--border-glass); color: var(--text-primary); font-weight: 500; padding: 0.35rem 0.8rem; border-radius: 20px; font-size: 0.85rem; }', css)

# Form Controls
css = re.sub(r'\.form-control,\s*\.form-select\s*\{[^\}]+\}', '.form-control, .form-select { background: var(--bg-primary); border: 1px solid var(--border-glass); color: var(--text-primary); border-radius: var(--radius-md); padding: 0.6rem 1rem; transition: var(--transition); box-shadow: none; }', css)
css = re.sub(r'\.form-control:focus,\s*\.form-select:focus\s*\{[^\}]+\}', '.form-control:focus, .form-select:focus { background: var(--bg-primary); border-color: var(--text-primary); box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.1); }', css)
css = re.sub(r'\[data-theme="dark"\] \.form-control:focus,\s*\[data-theme="dark"\] \.form-select:focus\s*\{[^\}]+\}', '[data-theme="dark"] .form-control:focus, [data-theme="dark"] .form-select:focus { background: var(--bg-primary) !important; border-color: var(--border-glow) !important; box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1) !important; }', css)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(css)
print('CSS updated successfully!')
