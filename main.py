import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QTreeView, QTextEdit, QLineEdit,
                               QPushButton, QLabel, QFileSystemModel,
                               QSplitter, QMessageBox, QMenu, QDialog,
                               QDialogButtonBox, QFormLayout, QListWidget,
                               QInputDialog, QFrame, QScrollArea, QGridLayout,
                               QCheckBox, QGraphicsDropShadowEffect)
from PySide6.QtGui import QAction, QFont, QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QDir, QItemSelectionModel, QSize, QPropertyAnimation, QEasingCurve


class FileCard(QFrame):
    def __init__(self, name, path, is_dir, parent=None):
        super().__init__(parent)
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setFixedSize(120, 100)

        # Добавляем тень для карточки
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Иконка (эмуляция)
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        if self.is_dir:
            icon_label.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388E3C);
                border-radius: 8px;
                color: white;
                font-weight: bold;
            """)
            icon_label.setText("📁")
        else:
            icon_label.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 8px;
                color: white;
                font-weight: bold;
            """)
            icon_label.setText("📄")
        icon_label.setAlignment(Qt.AlignCenter)

        # Название файла/папки
        name_label = QLabel(self.name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(110)
        name_label.setStyleSheet("font-size: 11px;")

        layout.addWidget(icon_label)
        layout.addWidget(name_label)

        # Стиль карточки
        self.setStyleSheet("""
            FileCard {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            FileCard:hover {
                background: #f5f5f5;
                border: 1px solid #2196F3;
            }
        """)


class RenameDialog(QDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Переименовать")
        self.setModal(True)
        self.resize(300, 100)

        layout = QFormLayout(self)

        self.old_name_label = QLabel(current_name)
        self.new_name_input = QLineEdit(current_name)

        layout.addRow("Текущее имя:", self.old_name_label)
        layout.addRow("Новое имя:", self.new_name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_new_name(self):
        return self.new_name_input.text().strip()


class GroupRenameDialog(QDialog):
    def __init__(self, file_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Групповое переименование")
        self.setModal(True)
        self.resize(400, 150)

        layout = QFormLayout(self)

        self.file_count_label = QLabel(f"Будет переименовано файлов: {file_count}")
        self.new_name_input = QLineEdit()
        self.new_name_input.setPlaceholderText("Введите новое базовое имя")

        layout.addRow(self.file_count_label)
        layout.addRow("Базовое имя:", self.new_name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_new_name(self):
        return self.new_name_input.text().strip()


class FileManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Файловый менеджер - Карточный интерфейс")
        self.resize(1200, 800)

        # Словарь для хранения выбранных карточек
        self.selected_cards = {}

        # Корневая папка main
        self.root_path = os.path.join(os.getcwd(), "main")
        os.makedirs(self.root_path, exist_ok=True)
        self.current_path = self.root_path

        self.setup_ui()
        self.setup_file_system()

    def setup_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Верхняя панель с навигацией
        self.setup_top_panel(main_layout)

        # Основная рабочая область
        self.setup_workspace(main_layout)

        # Панель команд
        self.setup_command_panel(main_layout)

        # Создаем меню
        self.create_menu()

    def setup_top_panel(self, main_layout):
        top_frame = QFrame()
        top_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        top_layout = QHBoxLayout(top_frame)

        # Кнопки навигации
        nav_layout = QHBoxLayout()

        self.home_button = QPushButton("🏠 Главная")
        self.home_button.setFixedWidth(100)
        self.home_button.clicked.connect(self.go_home)

        self.up_button = QPushButton("⬆️ Наверх")
        self.up_button.setFixedWidth(100)
        self.up_button.clicked.connect(self.go_up)

        self.refresh_button = QPushButton("🔄 Обновить")
        self.refresh_button.setFixedWidth(100)
        self.refresh_button.clicked.connect(self.refresh_view)

        nav_layout.addWidget(self.home_button)
        nav_layout.addWidget(self.up_button)
        nav_layout.addWidget(self.refresh_button)

        # Путь
        path_layout = QVBoxLayout()
        self.path_label = QLabel(f"Текущий путь: {self.get_relative_path()}")
        self.path_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")

        self.breadcrumb_label = QLabel(self.get_breadcrumb())
        self.breadcrumb_label.setStyleSheet("color: #E3F2FD; font-size: 10px;")

        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.breadcrumb_label)

        top_layout.addLayout(nav_layout)
        top_layout.addStretch()
        top_layout.addLayout(path_layout)

        main_layout.addWidget(top_frame)

    def setup_workspace(self, main_layout):
        workspace_splitter = QSplitter(Qt.Horizontal)

        # Левая панель - древовидное представление (свернуто по умолчанию)
        self.tree_panel = QWidget()
        tree_layout = QVBoxLayout(self.tree_panel)

        tree_header = QLabel("🌳 Дерево папок")
        tree_header.setStyleSheet("font-weight: bold; color: #1976D2;")
        tree_layout.addWidget(tree_header)

        self.tree_view = QTreeView()
        self.tree_view.setFont(QFont("Consolas", 9))
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree_view.setMaximumWidth(300)

        tree_layout.addWidget(self.tree_view)

        # Центральная панель - карточки файлов
        central_panel = QWidget()
        central_layout = QVBoxLayout(central_panel)

        # Панель инструментов карточек
        card_tools_layout = QHBoxLayout()

        self.view_mode_button = QPushButton("📋 Список")
        self.view_mode_button.setCheckable(True)
        self.view_mode_button.setFixedWidth(100)
        self.view_mode_button.clicked.connect(self.toggle_view_mode)

        self.select_all_checkbox = QCheckBox("Выбрать все")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)

        card_tools_layout.addWidget(self.view_mode_button)
        card_tools_layout.addStretch()
        card_tools_layout.addWidget(self.select_all_checkbox)

        central_layout.addLayout(card_tools_layout)

        # Область с карточками
        self.cards_scroll = QScrollArea()
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignTop)

        self.cards_scroll.setWidget(self.cards_widget)
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        central_layout.addWidget(self.cards_scroll)

        # Правая панель - информация
        info_panel = QFrame()
        info_panel.setFrameStyle(QFrame.Box)
        info_panel.setStyleSheet("""
            QFrame {
                background: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_panel)

        info_header = QLabel("📊 Информация")
        info_header.setStyleSheet("font-weight: bold; color: #1976D2; font-size: 14px;")
        info_layout.addWidget(info_header)

        self.info_text = QTextEdit()
        self.info_text.setFont(QFont("Consolas", 10))
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumWidth(350)

        info_layout.addWidget(self.info_text)

        # Настройка splitter
        workspace_splitter.addWidget(self.tree_panel)
        workspace_splitter.addWidget(central_panel)
        workspace_splitter.addWidget(info_panel)

        # Начальные размеры (дерево свернуто)
        workspace_splitter.setSizes([100, 700, 400])

        main_layout.addWidget(workspace_splitter)

    def setup_command_panel(self, main_layout):
        command_frame = QFrame()
        command_frame.setStyleSheet("""
            QFrame {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        command_layout = QHBoxLayout(command_frame)

        command_layout.addWidget(QLabel("💻 Команда:"))

        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.setPlaceholderText("Введите команду (помощь - для списка команд)")
        self.command_input.returnPressed.connect(self.execute_command)

        self.execute_button = QPushButton("Выполнить")
        self.execute_button.clicked.connect(self.execute_command)
        self.execute_button.setFixedWidth(100)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)

        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.execute_button)

        main_layout.addWidget(command_frame)

    def create_menu(self):
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        new_folder_action = QAction("📁 Создать папку", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        file_menu.addAction(new_folder_action)

        group_rename_action = QAction("🔄 Групповое переименование", self)
        group_rename_action.triggered.connect(self.group_rename_selected)
        file_menu.addAction(group_rename_action)

        file_menu.addSeparator()

        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.refresh_view)
        file_menu.addAction(refresh_action)

        exit_action = QAction("🚪 Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Вид
        view_menu = menubar.addMenu("Вид")

        toggle_tree_action = QAction("🌳 Показать/скрыть дерево", self)
        toggle_tree_action.triggered.connect(self.toggle_tree_view)
        view_menu.addAction(toggle_tree_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")

        help_action = QAction("❓ Справка по командам", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def setup_file_system(self):
        # Модель файловой системы
        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)
        self.model.setNameFilters([])
        self.model.setNameFilterDisables(False)

        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)

        self.update_info()
        self.update_cards_view()

    def get_relative_path(self):
        rel_path = os.path.relpath(self.current_path, start=self.root_path)
        return rel_path if rel_path != "." else "main"

    def get_breadcrumb(self):
        rel_path = self.get_relative_path()
        parts = rel_path.split(os.sep)
        return " > ".join(parts)

    def update_info(self):
        self.path_label.setText(f"Текущий путь: {self.get_relative_path()}")
        self.breadcrumb_label.setText(self.get_breadcrumb())
        self.show_dir_info()

    def show_dir_info(self):
        rel = self.get_relative_path()
        info_text = f"📂 <b>Текущая директория:</b> {rel}\n\n"

        try:
            entries = os.listdir(self.current_path)
            dirs = [e for e in entries if os.path.isdir(os.path.join(self.current_path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(self.current_path, e))]

            info_text += f"📁 <b>Папки:</b> {len(dirs)}\n"
            info_text += f"📄 <b>Файлы:</b> {len(files)}\n\n"

            if files:
                total_size = 0
                for f in files:
                    file_path = os.path.join(self.current_path, f)
                    total_size += os.path.getsize(file_path)
                info_text += f"📊 <b>Общий размер файлов:</b> {total_size} байт\n"

        except PermissionError:
            info_text += "❌ <b>Нет доступа к этой папке</b>"

        self.info_text.setText(info_text)

    def update_cards_view(self):
        # Очищаем предыдущие карточки
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.selected_cards.clear()

        try:
            entries = os.listdir(self.current_path)
            entries.sort()  # Сортируем для красивого отображения

            row, col = 0, 0
            max_cols = 6  # Максимальное количество карточек в строке

            for entry in entries:
                entry_path = os.path.join(self.current_path, entry)
                is_dir = os.path.isdir(entry_path)

                card = FileCard(entry, entry_path, is_dir)
                card.mousePressEvent = lambda event, c=card: self.on_card_clicked(c, event)
                card.mouseDoubleClickEvent = lambda event, p=entry_path: self.on_card_double_clicked(p, event)

                self.cards_layout.addWidget(card, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        except PermissionError:
            error_label = QLabel("❌ Нет доступа к этой папке")
            error_label.setStyleSheet("color: red; font-size: 16px;")
            self.cards_layout.addWidget(error_label, 0, 0)

    def on_card_clicked(self, card, event):
        if event.button() == Qt.LeftButton:
            # Ctrl для множественного выбора
            if event.modifiers() & Qt.ControlModifier:
                if card.path in self.selected_cards:
                    self.deselect_card(card)
                else:
                    self.select_card(card)
            else:
                # Одиночный выбор
                self.clear_selection()
                self.select_card(card)

    def on_card_double_clicked(self, path, event):
        if os.path.isdir(path):
            self.open_directory(path)

    def select_card(self, card):
        card.setStyleSheet("""
            FileCard {
                background: #E3F2FD;
                border: 2px solid #2196F3;
                border-radius: 8px;
            }
        """)
        self.selected_cards[card.path] = card

    def deselect_card(self, card):
        card.setStyleSheet("""
            FileCard {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            FileCard:hover {
                background: #f5f5f5;
                border: 1px solid #2196F3;
            }
        """)
        if card.path in self.selected_cards:
            del self.selected_cards[card.path]

    def clear_selection(self):
        for card in list(self.selected_cards.values()):
            self.deselect_card(card)
        self.selected_cards.clear()

    def toggle_select_all(self, state):
        if state == Qt.Checked:
            self.clear_selection()
            for i in range(self.cards_layout.count()):
                widget = self.cards_layout.itemAt(i).widget()
                if isinstance(widget, FileCard):
                    self.select_card(widget)
        else:
            self.clear_selection()

    def toggle_view_mode(self):
        if self.view_mode_button.isChecked():
            self.view_mode_button.setText("🃏 Карточки")
            # Здесь можно реализовать режим списка
        else:
            self.view_mode_button.setText("📋 Список")
            self.update_cards_view()

    def toggle_tree_view(self):
        if self.tree_panel.isVisible():
            self.tree_panel.hide()
        else:
            self.tree_panel.show()

    def go_home(self):
        self.current_path = self.root_path
        self.tree_view.setRootIndex(self.model.index(self.current_path))
        self.update_info()
        self.update_cards_view()

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if os.path.commonpath([parent, self.root_path]) != self.root_path:
            QMessageBox.warning(self, "Ошибка", "Нельзя подняться выше 'main'.")
        elif parent == self.current_path:
            QMessageBox.information(self, "Информация", "Вы уже в корне дерева.")
        else:
            self.current_path = parent
            self.tree_view.setRootIndex(self.model.index(self.current_path))
            self.update_info()
            self.update_cards_view()

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.open_directory(path)

    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        path = self.model.filePath(index)
        menu = QMenu(self)

        if os.path.isdir(path):
            rename_action = QAction("Переименовать", self)
            rename_action.triggered.connect(lambda: self.rename_item(path))
            menu.addAction(rename_action)

            open_action = QAction("Открыть", self)
            open_action.triggered.connect(lambda: self.open_directory(path))
            menu.addAction(open_action)
        else:
            rename_action = QAction("Переименовать файл", self)
            rename_action.triggered.connect(lambda: self.rename_item(path))
            menu.addAction(rename_action)

        selected_indexes = self.tree_view.selectionModel().selectedIndexes()
        if len(selected_indexes) > 1:
            group_rename_action = QAction("Групповое переименование выделенных", self)
            group_rename_action.triggered.connect(self.group_rename_selected)
            menu.addAction(group_rename_action)

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def rename_item(self, path):
        current_name = os.path.basename(path)
        dialog = RenameDialog(current_name, self)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            if new_name and new_name != current_name:
                try:
                    new_path = os.path.join(os.path.dirname(path), new_name)
                    os.rename(path, new_path)
                    self.refresh_view()
                    QMessageBox.information(self, "Успех", f"Успешно переименовано в: {new_name}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать: {e}")

    def group_rename_selected(self):
        """Групповое переименование выделенных файлов"""
        if not self.selected_cards:
            # Если ничего не выбрано в карточках, используем старый метод
            selected_indexes = self.tree_view.selectionModel().selectedIndexes()
            file_paths = []
            for index in selected_indexes:
                if index.column() == 0:
                    path = self.model.filePath(index)
                    if os.path.isfile(path):
                        file_paths.append(path)
        else:
            # Используем выбранные карточки
            file_paths = [path for path in self.selected_cards.keys()
                          if os.path.isfile(path)]

        if not file_paths:
            QMessageBox.information(self, "Информация", "Выберите файлы для переименования.")
            return

        file_paths.sort()
        dialog = GroupRenameDialog(len(file_paths), self)
        if dialog.exec_() == QDialog.Accepted:
            new_base_name = dialog.get_new_name()
            if not new_base_name:
                QMessageBox.warning(self, "Ошибка", "Введите базовое имя.")
                return

            self.perform_group_rename(file_paths, new_base_name)

    def perform_group_rename(self, file_paths, new_base_name):
        """Выполняет групповое переименование файлов"""
        success_count = 0
        warning_messages = []

        for i, old_path in enumerate(file_paths, 1):
            if not os.path.exists(old_path):
                warning_messages.append(f"Файл не существует: {os.path.basename(old_path)}")
                continue

            _, ext = os.path.splitext(old_path)
            new_name = f"{new_base_name}_{i}{ext}"
            new_path = os.path.join(os.path.dirname(old_path), new_name)

            try:
                os.rename(old_path, new_path)
                success_count += 1
            except Exception as e:
                warning_messages.append(f"Ошибка переименования {os.path.basename(old_path)}: {e}")

        result_message = f"Успешно переименовано: {success_count} файлов"
        if warning_messages:
            result_message += f"\n\nПредупреждения:\n" + "\n".join(warning_messages)

        QMessageBox.information(self, "Результат", result_message)
        self.refresh_view()

    def open_directory(self, path):
        self.current_path = path
        self.tree_view.setRootIndex(self.model.index(path))
        self.update_info()
        self.update_cards_view()

    def create_new_folder(self):
        name, ok = QInputDialog.getText(self, "Создать папку", "Введите имя папки:")
        if ok and name:
            try:
                new_folder_path = os.path.join(self.current_path, name)
                os.makedirs(new_folder_path, exist_ok=True)
                self.refresh_view()
                QMessageBox.information(self, "Успех", f"Папка '{name}' создана")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать папку: {e}")

    def refresh_view(self):
        self.model.setRootPath(self.root_path)
        self.tree_view.setRootIndex(self.model.index(self.current_path))
        self.update_info()
        self.update_cards_view()
        self.clear_selection()
        self.select_all_checkbox.setCheckState(Qt.Unchecked)

    def execute_command(self):
        command = self.command_input.text().strip()
        if not command:
            return

        self.command_input.clear()
        self.info_text.append(f"> {command}")

        parts = command.split()
        cmd = parts[0].lower() if parts else ""

        try:
            if cmd == "выход":
                self.close()

            elif cmd == "нд":
                self.go_up()

            elif cmd == "вд":
                if len(parts) < 2:
                    self.info_text.append("❌ Укажите имя папки.")
                    return

                target = os.path.join(self.current_path, parts[1])
                if os.path.isdir(target):
                    self.open_directory(target)
                else:
                    self.info_text.append("❌ Папка не найдена.")

            elif cmd == "имя":
                if len(parts) < 3:
                    self.info_text.append("❌ Использование: имя <старое> <новое>")
                    return

                old_name = os.path.join(self.current_path, parts[1])
                new_name_full = ' '.join(parts[2:])
                new_name = os.path.join(self.current_path, new_name_full)

                if not os.path.exists(old_name):
                    self.info_text.append("❌ Файл или папка не существует.")
                    return

                os.rename(old_name, new_name)
                self.info_text.append(f"✅ Переименовано: {parts[1]} → {new_name_full}")
                self.refresh_view()

            elif cmd == "имягр":
                if len(parts) < 3:
                    self.info_text.append("❌ Использование: имягр <новое> <имя1> <имя2> <имя3> ...")
                    return

                new_base_name = parts[1]
                file_names = parts[2:]

                self.execute_group_rename_command(new_base_name, file_names)

            elif cmd == "инфо":
                self.show_dir_info()

            elif cmd == "помощь":
                self.show_help()

            else:
                self.info_text.append("❌ Неизвестная команда.")
                self.show_help()

        except Exception as e:
            self.info_text.append(f"⚠️ Ошибка: {e}")

    def execute_group_rename_command(self, new_base_name, file_names):
        """Выполняет групповое переименование из командной строки"""
        success_count = 0
        warning_messages = []

        for i, file_name in enumerate(file_names, 1):
            old_path = os.path.join(self.current_path, file_name)

            if not os.path.exists(old_path):
                warning_messages.append(f"Файл не существует: {file_name}")
                continue

            _, ext = os.path.splitext(old_path)
            new_name = f"{new_base_name}_{i}{ext}"
            new_path = os.path.join(self.current_path, new_name)

            try:
                os.rename(old_path, new_path)
                success_count += 1
                self.info_text.append(f"✅ {file_name} → {new_name}")
            except Exception as e:
                warning_messages.append(f"Ошибка переименования {file_name}: {e}")

        for warning in warning_messages:
            self.info_text.append(f"⚠️ {warning}")

        if success_count > 0:
            self.info_text.append(f"✅ Успешно переименовано: {success_count} файлов")

        self.refresh_view()

    def show_help(self):
        help_text = """
🎯 <b>Доступные команды:</b>

  <b>Нд</b> - подняться на уровень вверх
  <b>Вд</b> <папка> - перейти в подпапку
  <b>имя</b> <старое> <новое> - переименовать файл/папку
  <b>имягр</b> <новое> <имя1> <имя2> ... - групповое переименование файлов
  <b>инфо</b> - показать содержимое текущей папки
  <b>помощь</b> - показать эту справку
  <b>выход</b> - закрыть программу

💡 <b>Советы:</b>
- Двойной клик по папке/карточке открывает её
- Выделяйте несколько файлов с помощью Ctrl+клик
- Используйте "Выбрать все" для массовых операций
- Дерево папок можно скрыть через меню "Вид"
- Карточный интерфейс упрощает визуальную навигацию
"""
        self.info_text.setText(help_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = FileManagerApp()
    window.show()

    sys.exit(app.exec())