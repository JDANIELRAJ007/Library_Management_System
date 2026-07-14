import os
import re

mapping = {
    'fa-book-open': 'book-open',
    'fa-chart-pie': 'pie-chart',
    'fa-users': 'users',
    'fa-book': 'book',
    'fa-plus-circle': 'plus-circle',
    'fa-tag': 'tag',
    'fa-hand-holding-heart': 'heart-handshake',
    'fa-rupee-sign': 'indian-rupee',
    'fa-chart-bar': 'bar-chart',
    'fa-chalkboard-teacher': 'graduation-cap',
    'fa-clipboard-check': 'clipboard-check',
    'fa-search': 'search',
    'fa-user-graduate': 'graduation-cap',
    'fa-user-cog': 'user-cog',
    'fa-home': 'home',
    'fa-file-pdf': 'file-text',
    'fa-heart': 'heart',
    'fa-history': 'history',
    'fa-bell': 'bell',
    'fa-globe': 'globe',
    'fa-external-link-alt': 'external-link',
    'fa-sign-out-alt': 'log-out',
    'fa-bars': 'menu',
    'fa-sun': 'sun',
    'fa-moon': 'moon',
    'fa-robot': 'bot',
    'fa-chevron-up': 'chevron-up',
    'fa-chevron-down': 'chevron-down',
    'fa-chevron-left': 'chevron-left',
    'fa-chevron-right': 'chevron-right',
    'fa-paper-plane': 'send',
    'fa-plus': 'plus',
    'fa-times': 'x',
    'fa-save': 'save',
    'fa-clipboard-list': 'clipboard-list',
    'fa-book-reader': 'book-open-check',
    'fa-exclamation-triangle': 'triangle-alert',
    'fa-check-double': 'check-circle-2',
    'fa-smile': 'smile',
    'fa-trash': 'trash',
    'fa-check': 'check',
    'fa-inbox': 'inbox',
    'fa-exclamation-circle': 'circle-alert',
    'fa-check-circle': 'check-circle',
    'fa-info-circle': 'info',
    'fa-bell-slash': 'bell-off',
}

def replace_icons(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        fa_class = match.group(1)
        # Handle cases where multiple classes are in the string, or style tags are present
        lucide_icon = mapping.get(fa_class, fa_class.replace('fa-', ''))
        return f'<i data-lucide="{lucide_icon}"'

    new_content = re.sub(r'<i class="fas\s+([^"]+)"', replacer, content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            replace_icons(os.path.join(root, file))
