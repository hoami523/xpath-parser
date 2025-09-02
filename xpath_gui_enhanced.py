import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
import os
from bs4 import BeautifulSoup
import re

class XPathEnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("XPath生成器")
        self.root.geometry("1200x800")
        
        # 主框架
        main_frame = ttk.Frame(root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件选择区域 - 简化布局
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.file_path = tk.StringVar()
        ttk.Label(file_frame, text="HTML:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.file_path, width=50).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="浏览", command=self.browse_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="分析", command=self.analyze_html).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="粘贴源码解析", command=self.show_paste_dialog).pack(side=tk.LEFT)
        
        # 创建两栏布局 - 移除右侧统计信息，合并到中间
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左侧：HTML树结构
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        tree_frame = ttk.LabelFrame(left_frame, text="HTML结构", padding="5")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # HTML树控制按钮
        tree_control_frame = ttk.Frame(tree_frame)
        tree_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(tree_control_frame, text="全部展开", command=self.expand_all_tree, width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(tree_control_frame, text="全部收起", command=self.collapse_all_tree, width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(tree_control_frame, text="高亮元素", command=self.highlight_tree_element, width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.toggle_button = ttk.Button(tree_control_frame, text="原始HTML", command=self.toggle_view_mode, width=10)
        self.toggle_button.pack(side=tk.LEFT)
        
        # HTML显示区域 - 树形视图和文本框
        self.html_tree = ttk.Treeview(tree_frame, columns=('attrs'), show='tree headings', height=15)
        self.html_tree.heading('#0', text='节点路径')
        self.html_tree.heading('attrs', text='属性')
        
        # 设置列宽
        self.html_tree.column('#0', width=200)
        self.html_tree.column('attrs', width=150)
        
        # HTML滚动条
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.html_tree.yview)
        self.html_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # 原始HTML文本框（初始隐藏）
        self.original_text = scrolledtext.ScrolledText(tree_frame, height=15, width=50)
        
        # 默认显示树形视图
        self.html_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧：XPath列表 + 详细信息
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # XPath框架
        xpath_frame = ttk.LabelFrame(right_frame, text="XPath列表", padding="5")
        xpath_frame.pack(fill=tk.BOTH, expand=True)
        
        # 简化XPath控制按钮
        xpath_control_frame = ttk.Frame(xpath_frame)
        xpath_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(xpath_control_frame, text="复制", command=self.copy_selected, width=6).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(xpath_control_frame, text="复制全部", command=self.copy_all, width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(xpath_control_frame, text="导出", command=self.export_to_file, width=6).pack(side=tk.LEFT)
        
        # XPath树形视图 - 简化列
        self.xpath_tree = ttk.Treeview(xpath_frame, columns=('type', 'xpath'), show='tree headings', height=12)
        self.xpath_tree.heading('#0', text='元素')
        self.xpath_tree.heading('type', text='类型')
        self.xpath_tree.heading('xpath', text='XPath表达式')
        
        # 设置列宽
        self.xpath_tree.column('#0', width=120)
        self.xpath_tree.column('type', width=60)
        self.xpath_tree.column('xpath', width=400)
        
        # XPath滚动条
        xpath_scrollbar = ttk.Scrollbar(xpath_frame, orient=tk.VERTICAL, command=self.xpath_tree.yview)
        self.xpath_tree.configure(yscrollcommand=xpath_scrollbar.set)
        
        self.xpath_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        xpath_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 详细信息区域 - 合并到右侧底部
        detail_frame = ttk.LabelFrame(right_frame, text="详细信息", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=8, width=50)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 存储数据
        self.soup = None
        self.all_xpaths = []
        self.html_nodes = {}  # 存储HTML节点信息
        self.node_mapping = {}  # XPath到树节点的映射
        self.original_html = ""  # 存储原始HTML内容
        self.view_mode = "structured"  # 当前显示模式：structured或original
        
        # 绑定事件
        self.xpath_tree.bind('<Double-1>', self.copy_selected)  # 双击复制XPath
        self.xpath_tree.bind('<Button-3>', self.show_xpath_context_menu)
        self.html_tree.bind('<Button-1>', self.on_tree_click)
        self.html_tree.bind('<Double-1>', self.on_tree_double_click)
        # self.html_tree.bind('<Button-3>', self.show_tree_context_menu)  # 暂时移除，因为没有实现
        
        # 创建右键菜单
        self.create_context_menus()
        
        # 设置标签样式
        self.setup_styles()
        
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.configure("Treeview", font=('Consolas', 9))
        style.configure("Treeview.Heading", font=('Consolas', 10, 'bold'))
        
    def create_context_menus(self):
        """创建右键菜单"""
        # XPath右键菜单
        self.xpath_menu = tk.Menu(self.root, tearoff=0)
        self.xpath_menu.add_command(label="复制XPath", command=self.copy_selected)
        self.xpath_menu.add_command(label="复制元素描述", command=self.copy_description)
        self.xpath_menu.add_separator()
        self.xpath_menu.add_command(label="复制所有XPath", command=self.copy_all)
        self.xpath_menu.add_command(label="复制ID路径", command=self.copy_id_xpaths)
        
        # HTML树右键菜单
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="展开", command=self.expand_selected)
        self.tree_menu.add_command(label="收起", command=self.collapse_selected)
        
    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="选择HTML文件",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.analyze_html()
            
    def analyze_html(self):
        """分析HTML文件"""
        if not self.file_path.get():
            messagebox.showwarning("警告", "请先选择HTML文件")
            return
            
        try:
            with open(self.file_path.get(), 'r', encoding='utf-8') as file:
                content = file.read()
            
            self.original_html = content  # 保存原始HTML
            self.soup = BeautifulSoup(content, 'lxml')
            self.build_html_tree()
            self.generate_all_xpaths()
            self.update_statistics()
            
            # 分析完成后自动展开第一层
            self.expand_first_level()
            
            # 更新原始HTML显示
            self.update_original_html_display()
            
        except Exception as e:
            messagebox.showerror("错误", f"分析HTML文件时出错:\n{str(e)}")
            
    def build_html_tree(self):
        """构建HTML树结构"""
        # 清空现有树
        for item in self.html_tree.get_children():
            self.html_tree.delete(item)
        self.html_nodes.clear()
        
        if not self.soup:
            return
            
        # 从body开始构建树
        body = self.soup.find('body')
        if body:
            self._build_tree_recursive(body, '')
        else:
            # 如果没有body，从html开始
            html = self.soup.find('html') or self.soup
            self._build_tree_recursive(html, '')
            
    def _build_tree_recursive(self, element, parent_id):
        """递归构建HTML树"""
        if not element or not hasattr(element, 'name'):
            return
            
        # 跳过注释和特殊节点
        if isinstance(element, str) or element.name is None:
            return
            
        # 创建节点ID
        node_id = f"{element.name}_{len(self.html_nodes)}"
        
        # 准备显示信息 - 简化属性显示
        attrs_text = self._format_attrs(element.attrs)
        
        # 添加到树
        display_text = f"<{element.name}>"
        if element.get('id'):
            display_text += f" #{element.get('id')}"
        elif element.get('class'):
            classes = ' '.join(element.get('class'))
            display_text += f" .{classes.split()[0]}"
            
        if parent_id:
            item_id = self.html_tree.insert(parent_id, 'end', node_id,
                                          text=display_text,
                                          values=(attrs_text,))
        else:
            item_id = self.html_tree.insert('', 'end', node_id,
                                          text=display_text,
                                          values=(attrs_text,))
        
        # 存储节点信息
        self.html_nodes[node_id] = {
            'element': element,
            'tag': element.name,
            'attrs': element.attrs,
            'item_id': item_id
        }
        
        # 递归处理子元素
        for child in element.children:
            if hasattr(child, 'name') and child.name:
                self._build_tree_recursive(child, node_id)
                
    def toggle_view_mode(self):
        """切换视图模式"""
        if self.view_mode == "structured":
            self.view_mode = "original"
            self.toggle_button.config(text="结构化")
            self.html_tree.pack_forget()
            self.original_text.pack(fill=tk.BOTH, expand=True)
        else:
            self.view_mode = "structured"
            self.toggle_button.config(text="原始HTML")
            self.original_text.pack_forget()
            self.html_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
    def update_original_html_display(self):
        """更新原始HTML显示"""
        if self.original_html:
            self.original_text.delete(1.0, tk.END)
            self.original_text.insert(1.0, self.original_html)
            
    def expand_first_level(self):
        """分析完成后自动展开第一层"""
        for item in self.html_tree.get_children():
            self.html_tree.item(item, open=True)
        
    def expand_all_tree(self):
        """展开所有树节点"""
        def expand_children(item):
            self.html_tree.item(item, open=True)
            for child in self.html_tree.get_children(item):
                expand_children(child)
                
        for item in self.html_tree.get_children():
            expand_children(item)
            
    def collapse_all_tree(self):
        """收起所有树节点"""
        def collapse_children(item):
            for child in self.html_tree.get_children(item):
                collapse_children(child)
            self.html_tree.item(item, open=False)
            
        for item in self.html_tree.get_children():
            collapse_children(item)
            
    def _format_attrs(self, attrs):
        """格式化属性显示"""
        if not attrs:
            return ""
            
        parts = []
        for key, value in attrs.items():
            if key == 'class':
                value = ' '.join(value) if isinstance(value, list) else str(value)
                if len(value) > 30:
                    value = value[:27] + "..."
            elif isinstance(value, list):
                value = ' '.join(str(v) for v in value)
            else:
                value = str(value)
                if len(value) > 30:
                    value = value[:27] + "..."
                    
            parts.append(f"{key}='{value}'")
            
        return ' '.join(parts)[:50]
        
    def _get_text_content(self, element):
        """获取文本内容"""
        text = element.get_text(strip=True)
        if len(text) > 30:
            text = text[:27] + "..."
        return text
        
    def generate_all_xpaths(self):
        """生成所有XPath"""
        # 清空现有结果
        for item in self.xpath_tree.get_children():
            self.xpath_tree.delete(item)
        self.all_xpaths.clear()
        self.node_mapping.clear()
            
        if not self.soup:
            return
            
        # 定义要分析的元素类型 - 简化配置
        element_configs = [
            {'tag': 'a', 'name': '链接'},
            {'tag': 'button', 'name': '按钮'},
            {'tag': 'input', 'name': '输入框'},
            {'tag': 'form', 'name': '表单'},
            {'tag': 'div', 'name': '容器'},
            {'tag': 'span', 'name': '文本'},
            {'tag': 'img', 'name': '图片'},
            {'tag': 'table', 'name': '表格'},
            {'tag': 'select', 'name': '下拉框'},
            {'tag': 'textarea', 'name': '文本域'},
            {'tag': 'h1', 'name': '标题'},
            {'tag': 'h2', 'name': '标题'},
            {'tag': 'h3', 'name': '标题'},
            {'tag': 'p', 'name': '段落'},
            {'tag': 'ul', 'name': '列表'},
            {'tag': 'li', 'name': '列表项'}
        ]
        
        counter = 1
        for config in element_configs:
            elements = self.soup.find_all(config['tag'])
            for idx, element in enumerate(elements[:8], 1):  # 限制每个类型最多8个
                xpaths = self.generate_element_xpaths(element, config['tag'])
                
                for xpath_type, xpath in xpaths.items():
                    # 使用元素类型作为显示文本
                    item_id = self.xpath_tree.insert('', 'end', text=config['name'],
                                                   values=(xpath_type, xpath))
                    
                    # 建立XPath到HTML节点的映射
                    tree_node = self._find_tree_node_for_element(element)
                    
                    self.all_xpaths.append({
                        'id': counter,
                        'type': xpath_type,
                        'element_type': config['name'],
                        'element_index': idx,
                        'xpath': xpath,
                        'tag': config['tag'],
                        'element': element,
                        'tree_node': tree_node,
                        'item_id': item_id
                    })
                    
                    # 建立映射关系
                    if tree_node:
                        self.node_mapping[item_id] = tree_node
                    
                    counter += 1
                    
    def _find_tree_node_for_element(self, element):
        """根据元素找到对应的树节点"""
        for node_id, node_info in self.html_nodes.items():
            if node_info['element'] == element:
                return node_id
        return None
        
    def get_element_description(self, element):
        """获取元素描述"""
        desc_parts = []
        
        # ID属性
        if element.get('id'):
            desc_parts.append(f"id='{element.get('id')}'")
            
        # Class属性
        if element.get('class'):
            classes = ' '.join(element.get('class'))
            desc_parts.append(f"class='{classes}'")
            
        # 文本内容
        text = element.get_text(strip=True)
        if text and len(text) <= 30:
            desc_parts.append(f"文本='{text}'")
            
        # 特定属性
        if element.name == 'a' and element.get('href'):
            href = element.get('href')
            if len(href) <= 50:
                desc_parts.append(f"href='{href}'")
        elif element.name == 'input':
            input_type = element.get('type', 'text')
            placeholder = element.get('placeholder', '')
            if placeholder:
                desc_parts.append(f"placeholder='{placeholder}'")
            desc_parts.append(f"type='{input_type}'")
        elif element.name == 'img' and element.get('alt'):
            desc_parts.append(f"alt='{element.get('alt')}'")
            
        return ', '.join(desc_parts) if desc_parts else f"<{element.name}>"
        
    def generate_element_xpaths(self, element, tag):
        """为元素生成XPath"""
        xpaths = {}
        
        # 1. ID优先的XPath
        if element.get('id'):
            xpaths['ID'] = f"//{tag}[@id='{element.get('id')}']"
            
        # 2. Class优先的XPath
        if element.get('class'):
            classes = ' '.join(element.get('class'))
            xpaths['Class'] = f"//{tag}[contains(@class,'{classes.split()[0]}')]"
            
        # 3. 属性组合路径
        attrs = []
        for attr in ['name', 'type', 'placeholder', 'href', 'alt', 'src']:
            if element.get(attr):
                attrs.append(f"@{attr}='{element.get(attr)}'")
        
        if attrs:
            xpaths['属性'] = f"//{tag}[{' and '.join(attrs)}]"
            
        # 4. 文本内容路径
        text = element.get_text(strip=True)
        if text and len(text) <= 50:
            xpaths['文本'] = f"//{tag}[text()='{text}']"
            
        # 5. 位置路径
        parent = element.find_parent()
        if parent:
            siblings = parent.find_all(tag, recursive=False)
            if len(siblings) > 1:
                position = siblings.index(element) + 1
                xpaths['位置'] = f"//{tag}[{position}]"
                
        return xpaths
        
    def update_statistics(self):
        """更新统计信息到详细信息区域"""
        if not self.all_xpaths:
            return
            
        # 统计信息
        stats = {}
        for item in self.all_xpaths:
            element_type = item['element_type']
            stats[element_type] = stats.get(element_type, 0) + 1
            
        stats_text = "【统计信息】\n"
        for element_type, count in stats.items():
            stats_text += f"{element_type}: {count}个\n"
        stats_text += f"\n总计: {len(self.all_xpaths)} 个XPath\n\n"
        
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, stats_text)
        
    def on_xpath_double_click(self, event):
        """双击XPath时高亮对应元素"""
        self.highlight_element()
        
    def highlight_element(self):
        """高亮选中的XPath对应的HTML元素"""
        selected = self.xpath_tree.selection()
        if not selected:
            return
            
        item_id = selected[0]
        if item_id in self.node_mapping:
            tree_node = self.node_mapping[item_id]
            
            # 清除之前的高亮
            self.clear_highlight()
            
            # 高亮对应的树节点
            self.html_tree.item(tree_node, tags=('highlight',))
            self.html_tree.tag_configure('highlight', background='yellow', foreground='red')
            
            # 确保节点可见
            self.html_tree.see(tree_node)
            
            # 展开到该节点
            self.expand_to_node(tree_node)
            
            # 显示详细信息
            self.show_element_details()
            
    def clear_highlight(self):
        """清除高亮"""
        for item in self.html_tree.tag_has('highlight'):
            self.html_tree.item(item, tags=())
            
    def expand_to_node(self, node_id):
        """展开到指定节点"""
        parent = self.html_tree.parent(node_id)
        while parent:
            self.html_tree.item(parent, open=True)
            parent = self.html_tree.parent(parent)
            
    def on_tree_click(self, event):
        """点击树节点时显示信息"""
        item = self.html_tree.identify_row(event.y)
        if item:
            self.show_tree_node_details(item)
            
    def on_tree_double_click(self, event):
        """双击HTML树时高亮对应的XPath"""
        if self.view_mode == "original":
            # 原始HTML模式下不处理双击事件
            return
            
        item = self.html_tree.identify_row(event.y)
        if item and item in self.html_nodes:
            self.highlight_corresponding_xpath(item)
            
    def show_tree_node_details(self, node_id):
        """显示树节点详细信息"""
        if node_id in self.html_nodes:
            node_info = self.html_nodes[node_id]
            element = node_info['element']
            
            details = f"标签: <{element.name}>\n"
            
            if element.attrs:
                details += "\n属性:\n"
                for key, value in element.attrs.items():
                    if key == 'class':
                        value = ' '.join(value) if isinstance(value, list) else str(value)
                    details += f"  {key}: {value}\n"
            
            text = element.get_text(strip=True)
            if text:
                details += f"\n文本内容:\n{text[:200]}"
                if len(text) > 200:
                    details += "..."
            
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(1.0, details)
            
    def show_element_details(self):
        """显示选中元素的详细信息"""
        selected = self.xpath_tree.selection()
        if not selected:
            return
            
        item_id = selected[0]
        for xpath_item in self.all_xpaths:
            if xpath_item['item_id'] == item_id:
                element = xpath_item['element']
                
                details = f"元素类型: {xpath_item['element_type']}\n"
                details += f"XPath: {xpath_item['xpath']}\n"
                details += f"标签: <{element.name}>\n"
                
                if element.attrs:
                    details += "\n属性:\n"
                    for key, value in element.attrs.items():
                        if key == 'class':
                            value = ' '.join(value) if isinstance(value, list) else str(value)
                        details += f"  {key}: {value}\n"
                
                text = element.get_text(strip=True)
                if text:
                    details += f"\n文本内容:\n{text[:200]}"
                    if len(text) > 200:
                        details += "..."
                
                self.detail_text.delete(1.0, tk.END)
                self.detail_text.insert(1.0, details)
                
                # 高亮原始HTML中对应的元素
                self.highlight_original_html(element)
                break
                
    def highlight_tree_element(self):
        """高亮选中的树元素"""
        selected = self.html_tree.selection()
        if selected:
            self.clear_highlight()
            self.html_tree.item(selected[0], tags=('highlight',))
            self.html_tree.tag_configure('highlight', background='lightblue', foreground='blue')
            
    def highlight_corresponding_xpath(self, tree_node_id):
        """根据HTML树节点高亮对应的XPath"""
        if self.view_mode == "original":
            # 原始HTML模式下，通过元素位置查找
            return
            
        if tree_node_id not in self.html_nodes:
            return
            
        target_element = self.html_nodes[tree_node_id]['element']
        
        # 清除之前的选择和高亮
        self.xpath_tree.selection_remove(self.xpath_tree.selection())
        
        # 查找对应的XPath项
        for xpath_item in self.all_xpaths:
            if xpath_item['element'] == target_element:
                # 选中对应的XPath
                xpath_item_id = xpath_item['item_id']
                self.xpath_tree.selection_set(xpath_item_id)
                self.xpath_tree.see(xpath_item_id)
                
                # 显示详细信息
                self.show_element_details()
                break
            
    def expand_selected(self):
        """展开选中的树节点"""
        selected = self.html_tree.selection()
        if selected:
            self.html_tree.item(selected[0], open=True)
            
    def collapse_selected(self):
        """收起选中的树节点"""
        selected = self.html_tree.selection()
        if selected:
            self.html_tree.item(selected[0], open=False)
            
    def show_xpath_context_menu(self, event):
        """显示XPath右键菜单"""
        item = self.xpath_tree.identify_row(event.y)
        if item:
            self.xpath_tree.selection_set(item)
            self.xpath_menu.post(event.x_root, event.y_root)
            
    def copy_selected(self):
        """复制选中的XPath"""
        selected = self.xpath_tree.selection()
        if selected:
            item = self.xpath_tree.item(selected[0])
            values = item['values']
            if len(values) >= 2:
                xpath = values[1]  # XPath在第二列（索引1）
                self.root.clipboard_clear()
                self.root.clipboard_append(xpath)
                messagebox.showinfo("成功", f"XPath已复制到剪贴板:\n{xpath}")
            else:
                messagebox.showwarning("警告", "无法获取XPath数据")
            

            
    def copy_all(self):
        """复制所有XPath"""
        if not self.all_xpaths:
            messagebox.showwarning("警告", "没有可复制的XPath")
            return
            
        all_xpaths_text = []
        for item in self.all_xpaths:
            all_xpaths_text.append(f"#{item['id']} [{item['element_type']}{item['element_index']}] {item['type']}: {item['xpath']}")
            
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(all_xpaths_text))
        messagebox.showinfo("成功", f"已复制 {len(self.all_xpaths)} 个XPath到剪贴板")
        
    def copy_description(self):
        """复制选中的元素描述"""
        selected = self.xpath_tree.selection()
        if selected:
            item = self.xpath_tree.item(selected[0])
            values = item['values']
            if len(values) >= 2:
                # 获取元素类型作为描述
                element_type = item['text']  # 第一列是元素类型
                xpath_type = values[0]       # 第二列是XPath类型
                xpath = values[1]            # 第三列是XPath
                description = f"{element_type} ({xpath_type}): {xpath}"
                self.root.clipboard_clear()
                self.root.clipboard_append(description)
                messagebox.showinfo("成功", f"元素描述已复制到剪贴板")
            else:
                messagebox.showwarning("警告", "无法获取元素描述")
                
    def copy_id_xpaths(self):
        """复制所有ID路径的XPath"""
        id_xpaths = [item['xpath'] for item in self.all_xpaths if item['type'] == 'ID']
        if id_xpaths:
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(id_xpaths))
            messagebox.showinfo("成功", f"已复制 {len(id_xpaths)} 个ID路径的XPath")
        else:
            messagebox.showinfo("提示", "没有找到ID路径的XPath")
        
    def highlight_original_html(self, element):
        """高亮原始HTML中对应的元素"""
        if not self.original_html or self.view_mode != "original":
            return
            
        try:
            import re
            
            # 清除之前的高亮
            self.original_text.tag_remove('highlight', 1.0, tk.END)
            
            # 获取元素的标签名和属性
            tag_name = element.name
            attrs = element.attrs
            
            # 构建更精确的匹配模式
            # 首先尝试通过id匹配
            if 'id' in attrs:
                element_id = attrs['id']
                pattern = f'<{tag_name}[^>]*id="{re.escape(str(element_id))}"[^>]*>.*?</{tag_name}>'
            elif 'class' in attrs:
                # 通过class匹配
                class_value = attrs['class']
                if isinstance(class_value, list):
                    class_str = ' '.join(class_value)
                else:
                    class_str = str(class_value)
                pattern = f'<{tag_name}[^>]*class="[^"]*{re.escape(class_str)}[^"]*"[^>]*>.*?</{tag_name}>'
            else:
                # 通过标签名和文本内容匹配
                element_text = element.get_text(strip=True)
                if element_text and len(element_text.strip()) > 0:
                    # 转义特殊字符
                    escaped_text = re.escape(element_text.strip()[:50])
                    pattern = f'<{tag_name}[^>]*>{escaped_text}.*?</{tag_name}>'
                else:
                    # 简单的标签匹配
                    pattern = f'<{tag_name}[^>]*>.*?</{tag_name}>'
            
            # 查找匹配
            matches = list(re.finditer(pattern, self.original_html, re.DOTALL | re.IGNORECASE))
            
            if matches:
                # 找到最匹配的（考虑元素位置）
                best_match = None
                min_distance = float('inf')
                
                # 获取元素在解析树中的位置信息
                parent = element.parent
                if parent:
                    siblings = parent.find_all(tag_name)
                    try:
                        element_index = siblings.index(element)
                    except ValueError:
                        element_index = 0
                else:
                    element_index = 0
                
                # 选择对应位置的匹配
                if len(matches) > element_index:
                    best_match = matches[element_index]
                else:
                    best_match = matches[0]
                
                if best_match:
                    start_pos = best_match.start()
                    end_pos = best_match.end()
                    
                    # 高亮对应元素
                    self.original_text.tag_add('highlight', 
                        f"1.0 + {start_pos} chars", 
                        f"1.0 + {end_pos} chars")
                    self.original_text.tag_configure('highlight', 
                        background='yellow', foreground='black')
                    
                    # 滚动到高亮位置
                    self.original_text.see(f"1.0 + {start_pos} chars")
                    
        except Exception as e:
            print(f"高亮失败: {e}")
            pass
        
    def export_to_file(self):
        """导出结果到文件"""
        if not self.all_xpaths:
            messagebox.showwarning("警告", "没有可导出的数据")
            return
            
        filename = filedialog.asksaveasfilename(
            title="导出XPath",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("XPath生成结果\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # 统计信息
                    stats = {}
                    for item in self.all_xpaths:
                        stats[item['element_type']] = stats.get(item['element_type'], 0) + 1
                        
                    f.write("【统计信息】\n")
                    for element_type, count in stats.items():
                        f.write(f"{element_type}: {count}个\n")
                    f.write(f"\n总计: {len(self.all_xpaths)} 个XPath\n\n")
                    
                    # 详细结果
                    f.write("【详细XPath】\n")
                    for item in self.all_xpaths:
                        f.write(f"{item['element_type']} #{item['element_index']} [{item['type']}]\n")
                        f.write(f"  {item['xpath']}\n\n")
                        
                messagebox.showinfo("成功", f"已导出到: {filename}")
                    
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
                
    def show_paste_dialog(self):
        """显示粘贴源码的对话框"""
        paste_window = tk.Toplevel(self.root)
        paste_window.title("粘贴HTML源码")
        paste_window.geometry("800x600")
        
        # 设置对话框为模态
        paste_window.transient(self.root)
        paste_window.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(paste_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题和说明
        title_label = ttk.Label(main_frame, text="粘贴HTML源码", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 5))
        
        info_label = ttk.Label(main_frame, text="请在下方文本框中粘贴您的HTML源码，然后点击解析按钮")
        info_label.pack(pady=(0, 10))
        
        # 创建文本框框架
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建文本框和滚动条
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        paste_text = tk.Text(text_frame, wrap=tk.NONE, yscrollcommand=text_scroll.set, 
                           font=('Consolas', 10), height=25)
        paste_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.config(command=paste_text.yview)
        
        # 添加示例按钮
        def insert_example():
            example_html = '''<!DOCTYPE html>
<html>
<head>
    <title>示例页面</title>
</head>
<body>
    <div class="container">
        <h1>欢迎使用XPath解析器</h1>
        <p>这是一个示例HTML页面。</p>
        <ul>
            <li>第一项</li>
            <li>第二项</li>
        </ul>
        <form id="myForm">
            <input type="text" name="username" placeholder="用户名">
            <button type="submit">提交</button>
        </form>
    </div>
</body>
</html>'''
            paste_text.delete(1.0, tk.END)
            paste_text.insert(1.0, example_html)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="插入示例", command=insert_example).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="清空", command=lambda: paste_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="解析", command=lambda: self.parse_pasted_html(paste_text.get(1.0, tk.END), paste_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=paste_window.destroy).pack(side=tk.RIGHT)
        
        # 设置焦点
        paste_text.focus_set()
        
        # 居中显示
        paste_window.update_idletasks()
        x = (paste_window.winfo_screenwidth() // 2) - (paste_window.winfo_width() // 2)
        y = (paste_window.winfo_screenheight() // 2) - (paste_window.winfo_height() // 2)
        paste_window.geometry(f"+{x}+{y}")
        
    def parse_pasted_html(self, html_content, dialog_window):
        """解析粘贴的HTML源码"""
        if not html_content.strip():
            messagebox.showwarning("警告", "请输入HTML源码")
            return
            
        try:
            # 保存原始HTML内容
            self.original_html = html_content
            
            # 解析HTML
            self.soup = BeautifulSoup(html_content, 'html.parser')
            
            # 清空文件路径输入框，以表示当前使用的是粘贴的源码
            self.file_path.set("通过源码粘贴")
            
            # 构建树形结构
            self.build_html_tree()
            
            # 生成XPath
            self.generate_all_xpaths()
            
            # 更新原始HTML显示
            self.update_original_html_display()
            
            # 展开第一层
            self.expand_first_level()
            
            # 关闭对话框
            dialog_window.destroy()
            
            messagebox.showinfo("成功", "HTML源码解析完成！")
            
        except Exception as e:
            messagebox.showerror("错误", f"解析HTML源码时出错:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = XPathEnhancedGUI(root)
    root.mainloop()