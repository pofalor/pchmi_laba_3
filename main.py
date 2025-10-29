import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton,
                               QLabel, QMessageBox, QMenu, QDialog, QDialogButtonBox,
                               QFormLayout, QInputDialog, QScrollArea, QFrame,
                               QGridLayout, QCheckBox)
from PySide6.QtGui import QAction, QFont
from PySide6.QtCore import Qt, Signal
import datetime


class FileCard(QFrame):
    # Объявляем сигнал для переименования файла
    file_renamed = Signal(str, str, str)  # file_path, old_name, new_name

    def __init__(self, file_path, root_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.root_path = root_path
        self.is_renaming = False
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setMinimumWidth(200)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Имя файла (кликабельно для переименования)
        self.name_label = QLabel(os.path.basename(self.file_path))
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("QLabel { color: blue; }")
        self.name_label.mouseDoubleClickEvent = self.start_rename
        layout.addWidget(self.name_label)

        # Поле для редактирования имени (изначально скрыто)
        self.name_edit = QLineEdit(os.path.basename(self.file_path))
        self.name_edit.setVisible(False)
        self.name_edit.returnPressed.connect(self.finish_rename)
        self.name_edit.editingFinished.connect(self.finish_rename)
        layout.addWidget(self.name_edit)

        # Дата изменения
        mod_time = os.path.getmtime(self.file_path)
        mod_date = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        date_label = QLabel(f"Изменен: {mod_date}")
        date_label.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
        layout.addWidget(date_label)

        # Теги (папки) - используем Flow Layout с ограничением 3 тега в строке
        tags_label = QLabel("Теги:")
        tags_label.setStyleSheet("QLabel { font-weight: bold; font-size: 10px; }")
        layout.addWidget(tags_label)

        # Получаем теги из пути относительно root_path
        rel_path = os.path.relpath(os.path.dirname(self.file_path), self.root_path)
        folders = rel_path.split(os.sep) if rel_path != '.' else []

        # Создаем контейнер для тегов с вертикальным layout
        self.tags_container = QWidget()
        tags_container_layout = QVBoxLayout(self.tags_container)
        tags_container_layout.setContentsMargins(0, 0, 0, 0)
        tags_container_layout.setSpacing(3)

        # Разбиваем теги на строки по 3 тега в каждой
        max_tags_per_line = 3
        for i in range(0, len(folders), max_tags_per_line):
            line_tags = folders[i:i + max_tags_per_line]

            # Создаем горизонтальный контейнер для одной строки тегов
            line_widget = QWidget()
            line_layout = QHBoxLayout(line_widget)
            line_layout.setContentsMargins(0, 0, 0, 0)
            line_layout.setSpacing(3)

            # Добавляем теги в текущую строку
            for folder in line_tags:
                tag_label = QLabel(f"📁 {folder}")
                tag_label.setStyleSheet(
                    "QLabel { background: #e0e0e0; padding: 2px 4px; border-radius: 3px; font-size: 9px; }")
                tag_label.setWordWrap(True)
                line_layout.addWidget(tag_label)

            # Добавляем растягивающий элемент в конец строки
            line_layout.addStretch()
            tags_container_layout.addWidget(line_widget)

        layout.addWidget(self.tags_container)
        layout.addStretch()

        # Обновляем высоту карточки в зависимости от количества тегов
        self.update_card_height()

    def update_card_height(self):
        # Базовая высота + дополнительная высота за теги
        base_height = 120
        rel_path = os.path.relpath(os.path.dirname(self.file_path), self.root_path)
        tag_count = len(rel_path.split(os.sep)) if rel_path != '.' else 0

        # Вычисляем количество строк тегов (по 3 тега в строке)
        lines_count = (tag_count + 2) // 3  # Округление вверх
        additional_height = lines_count * 25  # +25px за каждую строку тегов
        self.setMinimumHeight(base_height + additional_height)

    def start_rename(self, event):
        self.is_renaming = True
        self.name_label.setVisible(False)
        self.name_edit.setVisible(True)
        self.name_edit.selectAll()
        self.name_edit.setFocus()

    def finish_rename(self):
        if not self.is_renaming:
            return

        new_name = self.name_edit.text().strip()
        old_name = os.path.basename(self.file_path)

        if new_name and new_name != old_name:
            try:
                new_path = os.path.join(os.path.dirname(self.file_path), new_name)
                os.rename(self.file_path, new_path)
                self.file_path = new_path
                self.name_label.setText(new_name)
                # Испускаем сигнал с информацией о переименовании
                self.file_renamed.emit(self.file_path, old_name, new_name)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать: {e}")

        self.is_renaming = False
        self.name_edit.setVisible(False)
        self.name_label.setVisible(True)


class FilesView(QWidget):
    selection_changed = Signal(list)  # list of selected files

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.file_widgets = []  # Храним виджеты карточек с чекбоксами
        self._selected_files = set()
        self.setup_ui()
        self.refresh_files()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Файлы в текущей директории и поддиректориях:"))
        title_layout.addStretch()

        # Кнопка выбора всех файлов
        self.select_all_btn = QPushButton("Выбрать все")
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        title_layout.addWidget(self.select_all_btn)

        layout.addLayout(title_layout)

        # Область прокрутки для карточек
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)

        layout.addWidget(self.scroll_area)

    def refresh_files(self):
        # Очищаем старые карточки
        for widget in self.file_widgets:
            widget.setParent(None)
            widget.deleteLater()

        self.file_widgets = []
        self._selected_files.clear()

        # Собираем все файлы рекурсивно
        all_files = []
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

        # Создаем карточки для файлов
        for i, file_path in enumerate(all_files):
            card = FileCard(file_path, self.root_path, self)
            # Подключаем сигнал переименования
            card.file_renamed.connect(self.on_file_renamed)

            # Добавляем чекбокс для выбора
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, fp=file_path, cb=checkbox: self.on_file_selected(fp, state, cb))

            card_widget = QWidget()
            card_layout = QVBoxLayout(card_widget)
            card_layout.setContentsMargins(5, 5, 5, 5)
            card_layout.addWidget(checkbox)
            card_layout.addWidget(card)

            self.file_widgets.append(card_widget)

            row = i // 4
            col = i % 4
            self.grid_layout.addWidget(card_widget, row, col)

        # Обновляем состояние кнопки выбора всех
        self.update_select_all_button()

    def on_file_renamed(self, file_path, old_name, new_name):
        # Обновляем интерфейс при переименовании файла
        self.refresh_files()

    def on_file_selected(self, file_path, state, checkbox):
        if checkbox.checkState() == Qt.Checked:
            self._selected_files.add(file_path)
        else:
            self._selected_files.discard(file_path)

        self.selection_changed.emit(list(self._selected_files))
        self.update_select_all_button()

    def update_select_all_button(self):
        # Обновляем текст кнопки "Выбрать все"
        if len(self._selected_files) == len(self.file_widgets) and len(self.file_widgets) > 0:
            self.select_all_btn.setText("Снять выделение")
        else:
            self.select_all_btn.setText("Выбрать все")

    def toggle_select_all(self):
        if len(self._selected_files) == len(self.file_widgets):
            # Снимаем выделение со всех
            for widget in self.file_widgets:
                checkbox = widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(False)
        else:
            # Выделяем все
            for widget in self.file_widgets:
                checkbox = widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(True)

    @property
    def selected_files(self):
        return list(self._selected_files)


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
        self.setWindowTitle("Файловый менеджер")
        self.resize(1200, 800)

        # Корневая папка main
        self.root_path = os.path.join(os.getcwd(), "main")
        os.makedirs(self.root_path, exist_ok=True)
        self.current_path = self.root_path

        self.setup_ui()

    def setup_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)

        # Панель пути и кнопок
        control_layout = QHBoxLayout()

        self.path_label = QLabel(f"Текущий путь: {self.get_relative_path()}")
        self.path_label.setFont(QFont("Arial", 10))

        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.refresh_view)
        self.refresh_button.setFixedWidth(80)

        self.group_rename_btn = QPushButton("Переименовать группу")
        self.group_rename_btn.clicked.connect(self.group_rename_selected)
        self.group_rename_btn.setFixedWidth(150)
        self.group_rename_btn.setEnabled(False)

        control_layout.addWidget(self.path_label)
        control_layout.addStretch()
        control_layout.addWidget(self.group_rename_btn)
        control_layout.addWidget(self.refresh_button)

        main_layout.addLayout(control_layout)

        # Виджет для отображения файлов в виде карточек
        self.files_view = FilesView(self.root_path)
        self.files_view.selection_changed.connect(self.on_selection_changed)
        main_layout.addWidget(self.files_view)

        # Создаем меню
        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        new_folder_action = QAction("Создать папку", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        file_menu.addAction(new_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")

        help_action = QAction("Справка", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def get_relative_path(self):
        rel_path = os.path.relpath(self.current_path, start=self.root_path)
        return rel_path if rel_path != "." else "main"

    def refresh_view(self):
        self.files_view.refresh_files()
        self.path_label.setText(f"Текущий путь: {self.get_relative_path()}")

    def on_selection_changed(self, selected_files):
        # Активируем кнопку, если есть выбранные файлы
        self.group_rename_btn.setEnabled(len(selected_files) > 0)

    def group_rename_selected(self):
        """Групповое переименование выделенных файлов через интерфейс"""
        selected_files = self.files_view.selected_files

        if not selected_files:
            QMessageBox.information(self, "Информация", "Выберите файлы для переименования.")
            return

        # Сортируем файлы по имени для последовательной нумерации
        selected_files = sorted(selected_files)

        dialog = GroupRenameDialog(len(selected_files), self)
        if dialog.exec() == QDialog.Accepted:
            new_base_name = dialog.get_new_name()
            if not new_base_name:
                QMessageBox.warning(self, "Ошибка", "Введите базовое имя.")
                return

            self.perform_group_rename(selected_files, new_base_name)

    def perform_group_rename(self, file_paths, new_base_name):
        """Выполняет групповое переименование файлов"""
        success_count = 0
        warning_messages = []

        for i, old_path in enumerate(file_paths, 1):
            if not os.path.exists(old_path):
                warning_messages.append(f"Файл не существует: {os.path.basename(old_path)}")
                continue

            # Получаем расширение файла
            _, ext = os.path.splitext(old_path)

            # Формируем новое имя: базовое_имя_номер.расширение
            new_name = f"{new_base_name}_{i}{ext}"
            new_path = os.path.join(os.path.dirname(old_path), new_name)

            try:
                os.rename(old_path, new_path)
                success_count += 1
            except Exception as e:
                warning_messages.append(f"Ошибка переименования {os.path.basename(old_path)}: {e}")

        # Показываем результаты
        result_message = f"Успешно переименовано: {success_count} файлов"
        if warning_messages:
            result_message += f"\n\nПредупреждения:\n" + "\n".join(warning_messages)

        QMessageBox.information(self, "Результат", result_message)
        self.refresh_view()

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

    def show_help(self):
        help_text = """
💡 Руководство по использованию:

• Двойной клик по имени файла - переименование (как в проводнике Windows)
• Чекбоксы - для выбора нескольких файлов
• Кнопка "Выбрать все" - выделяет/снимает выделение со всех файлов
• Кнопка "Переименовать группу" - групповое переименование выбранных файлов
• Кнопка "Обновить" - обновляет список файлов

📝 Групповое переименование:
1. Выберите файлы с помощью чекбоксов
2. Нажмите "Переименовать группу"
3. Введите базовое имя
4. Файлы будут переименованы в формате: базовое_имя_1.расширение, базовое_имя_2.расширение и т.д.
"""
        QMessageBox.information(self, "Справка", help_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Современный стиль

    window = FileManagerApp()
    window.show()

    sys.exit(app.exec())