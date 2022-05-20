from matplotlib.backend_bases import Gcf
from matplotlib.backends.backend_agg import FigureCanvasAgg
import logging
from chesster.gui import image_plot_signal

logger = logging.getLogger(__name__)
FigureCanvas = FigureCanvasAgg
managers_id = []


def show(*args, **kwargs):
    for num, fig_manager in enumerate(Gcf.get_all_fig_managers()):
        if fig_manager.num not in managers_id:
            managers_id.append(fig_manager.num)
            image_plot_signal.emit(num, fig_manager.canvas.figure)
            Gcf.destroy(num)
