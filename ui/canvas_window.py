import os
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QDialog, QPushButton, QVBoxLayout, QLineEdit, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QTransform, QPen
from PyQt5.QtCore import pyqtSignal, Qt, QRectF


class CanvasWindow(QDialog):
    save_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self, input_image, canvas_width=512, canvas_height=512):
        super().__init__()

        self.setWindowTitle("PyQt5 Image Canvas")
        self.input_image = input_image
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.modified_image = None

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("border: 1px solid black;")

        # 设置滚动条策略为需要时显示
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建白色画布
        self.canvas = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        self.canvas.fill(QColor('white'))

        # 添加画布背景
        self.canvas_pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(self.canvas))
        self.scene.addItem(self.canvas_pixmap_item)

        # 添加可调整大小和可旋转的输入图像
        scaled_pixmap = QPixmap.fromImage(self.input_image).scaled(
            self.canvas_width, self.canvas_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.input_pixmap_item = ResizablePixmapItem(scaled_pixmap, self.canvas_width, self.canvas_height)
        self.scene.addItem(self.input_pixmap_item)

        # 设置旋转锚点为图像中心
        self.input_pixmap_item.setTransformOriginPoint(self.input_pixmap_item.boundingRect().center())

        # 添加画布边界线
        self.add_canvas_border()

        # 创建按钮和输入框
        save_button = QPushButton("保存并关闭", self)
        save_button.clicked.connect(self.save_and_close)

        rotate_label = QLineEdit(self)
        rotate_label.setPlaceholderText("旋转角度 (°)")
        rotate_label.setFixedWidth(100)
        self.rotate_input = rotate_label

        rotate_button = QPushButton("旋转", self)
        rotate_button.clicked.connect(self.rotate_image)

        self.canvas_width_input = QLineEdit(self)
        self.canvas_width_input.setPlaceholderText("画布宽度")
        self.canvas_width_input.setText(str(self.canvas_width))
        self.canvas_height_input = QLineEdit(self)
        self.canvas_height_input.setPlaceholderText("画布高度")
        self.canvas_height_input.setText(str(self.canvas_height))

        size_button = QPushButton("设置画布大小", self)
        size_button.clicked.connect(self.set_canvas_size)

        # 布局设置
        hbox = QHBoxLayout()
        hbox.addWidget(self.canvas_width_input)
        hbox.addWidget(self.canvas_height_input)
        hbox.addWidget(size_button)
        hbox.addWidget(self.rotate_input)
        hbox.addWidget(rotate_button)

        vbox = QVBoxLayout()
        vbox.addWidget(self.view)
        vbox.addLayout(hbox)
        vbox.addWidget(save_button)

        self.setLayout(vbox)

        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

        # 设置窗口最小大小
        self.setMinimumSize(400, 300)

    def add_canvas_border(self):
        """添加画布边界线以可视化画布边缘"""
        pen = QPen(QColor('red'))
        pen.setWidth(2)
        border_rect = QRectF(0, 0, self.canvas_width, self.canvas_height)
        self.border_item = self.scene.addRect(border_rect, pen)
        self.border_item.setZValue(1)  # 确保边界线在最上层
        self.border_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.border_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.border_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)

    def save_and_close(self):
        self.save_image()
        self.accept()

    def save_image(self):
        # 创建一个与画布大小相同的图像
        image = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        image.fill(QColor('white'))

        painter = QPainter(image)
        target_rect = QRectF(0, 0, self.canvas_width, self.canvas_height)

        # 隐藏边界线
        self.border_item.setVisible(False)

        # 渲染场景
        self.scene.render(painter, target_rect, self.scene.sceneRect(), Qt.IgnoreAspectRatio)

        # 显示边界线
        self.border_item.setVisible(True)

        painter.end()

        self.modified_image = image

        # 保存路径
        save_directory = os.path.join(os.getcwd(), "ComfyUI", "custom_nodes", "ComfyUI-Snap_Processing", "save")

        timestamp = int(time.time() * 1000)
        save_path = os.path.join(save_directory, f"output_{timestamp}.png")
        image.save(save_path)
        self.save_signal.emit()

    def closeEvent(self, event):
        self.close_signal.emit()
        event.accept()

    def set_canvas_size(self):
        try:
            width = int(self.canvas_width_input.text())
            height = int(self.canvas_height_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "画布宽度和高度必须是整数。")
            return

        self.canvas_width = width
        self.canvas_height = height

        # 更新画布图像
        self.canvas = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        self.canvas.fill(QColor('white'))
        self.canvas_pixmap_item.setPixmap(QPixmap.fromImage(self.canvas))

        # 更新场景和视图
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

        # 更新边界线
        self.scene.removeItem(self.border_item)
        self.add_canvas_border()

        # 更新视图大小以适应新的画布大小
        self.view.updateGeometry()

    def rotate_image(self):
        try:
            angle = float(self.rotate_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "旋转角度必须是数字。")
            return

        self.input_pixmap_item.rotate_pixmap(angle)

    def get_modified_image(self):
        return self.modified_image


class ResizablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, canvas_width, canvas_height):
        super().__init__(pixmap)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.is_resizing = False
        self.resize_handle_size = 15  # 增大缩放手柄大小，便于操作
        self.aspect_ratio = pixmap.width() / pixmap.height() if pixmap.height() != 0 else 1
        self.setCursor(Qt.OpenHandCursor)
        self.min_scale = 0.1
        self.max_scale = 10
        self.current_scale = 1.0
        self.current_rotation = 0  # 当前旋转角度

        # 设置旋转锚点为图像中心
        self.setTransformOriginPoint(self.boundingRect().center())

    def hoverMoveEvent(self, event):
        if self.is_in_resize_area(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.OpenHandCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_in_resize_area(event.pos()):
            self.is_resizing = True
            self.resize_start_pos = event.pos()
            self.setCursor(Qt.SizeFDiagCursor)
            event.accept()
        else:
            self.is_resizing = False
            self.setCursor(Qt.ClosedHandCursor)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            offset = event.pos() - self.resize_start_pos
            self.resize_image(offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
        else:
            self.setCursor(Qt.OpenHandCursor)
            super().mouseReleaseEvent(event)

    def boundingRect(self):
        return QRectF(0, 0, self.pixmap().width(), self.pixmap().height())

    def resize_image(self, offset):
        # 调整缩放灵敏度
        scale_change = offset.x() / 500.0  # 增加分母以减少灵敏度
        scale_factor = 1 + scale_change
        if scale_factor <= 0:
            return  # 防止缩放为零或负值

        new_scale = self.current_scale * scale_factor

        if self.min_scale <= new_scale <= self.max_scale:
            self.current_scale = new_scale
            self.setScale(self.current_scale)
            self.update()

    def is_in_resize_area(self, pos):
        rect = self.boundingRect()
        resize_rect = QRectF(
            rect.right() - self.resize_handle_size,
            rect.bottom() - self.resize_handle_size,
            self.resize_handle_size,
            self.resize_handle_size
        )
        return resize_rect.contains(pos)

    def wheelEvent(self, event):
        try:
            if hasattr(event, 'angleDelta'):
                delta = event.angleDelta().y()
            elif hasattr(event, 'delta'):
                delta = event.delta()
            else:
                delta = 0

            factor = 1.1 if delta > 0 else 0.9
            self.resize_with_factor(factor)
        except AttributeError:
            pass

    def resize_with_factor(self, factor):
        new_scale = self.current_scale * factor

        if self.min_scale <= new_scale <= self.max_scale:
            self.current_scale = new_scale
            self.setScale(self.current_scale)
            self.update()

    def rotate_pixmap(self, angle):
        """根据输入角度旋转图像"""
        self.current_rotation = (self.current_rotation + angle) % 360
        self.setRotation(self.current_rotation)


# 示例用法
def run_pyqt_gui(input_image_path, canvas_width=512, canvas_height=512):
    app = QApplication(sys.argv)

    input_image = QImage(input_image_path)
    if input_image.isNull():
        QMessageBox.critical(None, "加载失败", "无法加载图像。请检查图像路径是否正确。")
        sys.exit(1)

    dialog = CanvasWindow(input_image, canvas_width, canvas_height)
    dialog.show()  # 使用 show 而不是 exec_ 以避免阻塞

    # 运行应用程序的事件循环
    app.exec_()

    modified_image = dialog.get_modified_image()
    if modified_image:
        save_directory = os.path.join(os.getcwd(), "ComfyUI", "custom_nodes", "Comfyui-Snap_Processing", "save")

        timestamp = int(time.time() * 1000)
        save_path = os.path.join(save_directory, f"modified_output_{timestamp}.png")
        modified_image.save(save_path)
    else:
        QMessageBox.information(None, "信息", "没有修改后的图像可用。")


if __name__ == "__main__":
    # 替换为您实际的图像路径
    image_path = "path_to_your_image.png"  # 请替换为实际图像路径
    run_pyqt_gui(image_path)
