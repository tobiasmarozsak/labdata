import cmasher
import colorcet
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients
import seaborn


for name, gradient in Gradients.items():
    colors = sorted(
        (level, tuple(channel / 256 for channel in color[:3]))
        for level, color in gradient["ticks"]
    )
    mpl.colormaps.register(
        LinearSegmentedColormap.from_list(f"qt_{name}", colors),
        name=f"qt_{name}",
    )
