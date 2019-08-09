from PySide2.QtCore import QRect, QRectF, Qt, QPointF
from PySide2.QtGui import QPainter, QPaintEvent, QColor, QLinearGradient, QFont
from PySide2.QtWidgets import QWidget

from backend.backend import Backend
from core.monitor_model import MonitorModel


class MonitorOverview(QWidget):

    def __init__(self, backend: Backend, parent=None):
        super().__init__(parent=parent)

        self.backend = backend
        self.backend.get_monitor_model().item_added.connect(self._item_added)
        self.backend.get_monitor_model().item_removed.connect(self._item_removed)
        self.backend.get_monitor_model().model_reset.connect(self._reset)

        self.vscreen_width = 0
        self.vscreen_height = 0
        self.vscreen_ratio = 1

        self._working_area = 0.75

        self.x_offset = 0
        self.y_offset = 0

        self._reset(model_reset=False)

        self.background_color = QColor(100, 100, 100)
        self.monitor_border_width = 30
        self.monitor_index_font = QFont('Arial')
        self.monitor_index_font_color = Qt.white
        self.monitor_color_gradient_top = QColor(70, 161, 84)
        self.monitor_color_gradient_bottom = QColor(59, 128, 169)

        self.__working_area_ratio = (1 - self._working_area) * 0.5

    def _reset(self, model_reset=True):
        self.vscreen_width, self.vscreen_height = self.backend.get_vscreen_size()
        self.x_offset, self.y_offset = self.backend.get_vscreen_normalize_offset()
        self.vscreen_ratio = self.vscreen_width / self.vscreen_height

        if model_reset:
            self.update()

    def _item_added(self, index, item):
        self._reset()

    def _item_removed(self, index, item):
        self._reset()

    def paintEvent(self, event: QPaintEvent):
        qp = QPainter()
        qp.begin(self)
        self.draw_widget(qp)
        qp.end()

    def draw_widget(self, painter: QPainter):
        view_width = self.width()
        view_height = self.height()

        # fill background
        painter.fillRect(QRect(0, 0, view_width, view_height), self.background_color)

        # create aspect-ratio-constant working area
        working_area = QRectF(self.__working_area_ratio * view_width, self.__working_area_ratio * view_height,
                              self._working_area * view_width, self._working_area * view_height)

        _ratio = working_area.width() / self.vscreen_width
        h = _ratio * self.vscreen_height
        if h > view_height:
            _ratio = working_area.height() / self.vscreen_height

        w = _ratio * self.vscreen_width
        h = _ratio * self.vscreen_height

        offset_x = working_area.left() + ((working_area.width() - w) / 2)
        offset_y = working_area.top() + ((working_area.height() - h) / 2)

        # Set border color
        pen = painter.pen()
        pen.setWidthF(self.monitor_border_width * _ratio)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)

        # Draw for each monitor corresponding
        monitor: MonitorModel
        for monitor in self.backend.monitor_model:
            # calculate position of monitor in canvas
            pos_x = offset_x + _ratio * (monitor.position_x - self.x_offset)
            pos_y = offset_y + _ratio * (monitor.position_y - self.y_offset)
            size_x = _ratio * monitor.screen_width
            size_y = _ratio * monitor.screen_height
            rect_monitor = QRectF(pos_x, pos_y, size_x, size_y)

            # put gradient in the background
            gradient = QLinearGradient(rect_monitor.topRight(), rect_monitor.bottomLeft())

            gradient.setColorAt(0.0, self.monitor_color_gradient_top)
            gradient.setColorAt(1.0, self.monitor_color_gradient_bottom)
            painter.fillRect(rect_monitor, gradient)

            # draw numbers
            painter.save()
            painter.setPen(self.monitor_index_font_color)
            painter.setFont(self.monitor_index_font)
            self._font_size_for_rect(painter, rect_monitor, monitor.index)
            painter.drawText(rect_monitor, Qt.AlignCenter, monitor.index)

            # Primary display
            if monitor.primary:
                font = painter.font()
                font.setPointSizeF(font.pointSizeF() / 2)
                painter.setFont(font)
                _w = painter.fontMetrics().height()
                rect = QRectF(rect_monitor.right(), rect_monitor.top(), -_w, _w)
                painter.drawText(rect, Qt.AlignCenter, '*')
            painter.restore()

            # draw borders inside rect
            border_offset = painter.pen().widthF() / 2
            painter.drawLine(QPointF(rect_monitor.left(), rect_monitor.top() + border_offset),
                             QPointF(rect_monitor.right(), rect_monitor.top() + border_offset))
            painter.drawLine(QPointF(rect_monitor.right() - border_offset, rect_monitor.top()),
                             QPointF(rect_monitor.right() - border_offset, rect_monitor.bottom()))
            painter.drawLine(QPointF(rect_monitor.right(), rect_monitor.bottom() - border_offset),
                             QPointF(rect_monitor.left(), rect_monitor.bottom() - border_offset))
            painter.drawLine(QPointF(rect_monitor.left() + border_offset, rect_monitor.bottom()),
                             QPointF(rect_monitor.left() + border_offset, rect_monitor.top()))

    # noinspection PyMethodMayBeStatic
    def _font_size_for_rect(self, painter: QPainter, rect: QRectF, txt: str):
        font_factor = rect.width() / painter.fontMetrics().width(txt)
        font = painter.font()
        font.setPointSizeF(font.pointSizeF() * font_factor)
        painter.setFont(font)
        if painter.fontMetrics().height() > rect.height():
            font_factor = rect.height() / painter.fontMetrics().height()
        font.setPointSizeF(font.pointSizeF() * font_factor)
        painter.setFont(font)
