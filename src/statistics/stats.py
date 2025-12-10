import numpy as np 
import pandas as pd 
import geopandas as gpd

import seaborn as sns
import contextily as ctx
import matplotlib.colors
import matplotlib.pyplot as plt
import matplotlib.colors as colors

sns.set_style("darkgrid")

def calculate_stats(data, group_fields):
    """
    code based on Ookla's Github repository tutorials
    https://github.com/teamookla/ookla-open-data/blob/master/tutorials
    calculates weighted average of the download and upload speeds and total tests

    Parameters
    ----------
    data : GeoDataFrame) 
        geo pandas dataframe to analyze
    group_fields : list
        list of fields to group by

    Returns
    ----------
    geopandas.GeoDataFrame
        GeoDataFrame with the calculated stats
    """
    
    return (
        data.groupby(group_fields)
        .apply(
            lambda x: pd.Series(
                {"avg_d_mbps_wt": np.average(x["avg_d_mbps"], weights=x["tests"]),
                "avg_u_mbps_wt": np.average(x["avg_u_mbps"], weights=x["tests"])
                }
            )
        )
        .reset_index()
        .merge(
            data.groupby(group_fields)
            .agg(tests=("tests", "sum"))
            .reset_index(),
            on=group_fields,
        )
    )

# Define color palettes
color_sets = {
    'pink-blue'  :['#e8e8e8','#ace4e4','#5ac8c8','#dfb0d6','#a5add3','#5698b9','#be64ac','#8c62aa','#3b4994'],
    'teal-red'   :['#e8e8e8','#b0d5df','#64acbe','#e4acac','#ad9ea5','#627f8c','#c85a5a','#985356','#574249'],
    'blue-orange':['#fef1e4','#fab186','#f3742d','#97d0e7','#b0988c','#ab5f37','#18aee5','#407b8f','#5c473d'],
    'yellow-red' :['#ffffe0','#ffcc99','#ff9966','#ff6666','#ff3333','#ff0000','#cc0000','#990000','#660000'],
    'blue-red'   :['#0000ff','#3333ff','#6666ff','#9999ff','#ccccff','#ffcccc','#ff9999','#ff6666','#ff3333'],
    'reds'       :['#ffcccc','#ff9999','#ff6666','#ff3333','#ff0000','#cc0000','#990000','#800000','#660000'],
    'cividis'    :['#00224e','#1a386f','#434e6c','#61656f','#7d7c78','#9b9476','#bcae6c','#dec958','#fee838']
}

def palettes():
    # Figure with all the palettes
    fig, axes = plt.subplots(nrows = 1, ncols = len(color_sets), figsize = (20, 8))
    
    for ax, (name, colors_) in zip(axes, color_sets.items()):
        matrix = np.arange(9).reshape((3, 3))
        cmap   = colors.ListedColormap(colors_)
        ax.imshow(matrix, cmap=cmap, origin='lower')
        ax.set_title(name, fontsize=15)
        ax.axis('off')
    
    plt.tight_layout()
    plt.show()

def expand_colors(base_colors, new_size):
    original_size = int(len(base_colors)**0.5)
    assert new_size > original_size, "New size must be larger than original size"
    
    new_colors = []
    for i in range(new_size):
        for j in range(new_size):
            x = i / (new_size - 1) * (original_size - 1)
            y = j / (new_size - 1) * (original_size - 1)
            x0, x1 = int(x), min(int(x) + 1, original_size - 1)
            y0, y1 = int(y), min(int(y) + 1, original_size - 1)
            
            f00 = base_colors[x0 * original_size + y0]
            f01 = base_colors[x0 * original_size + y1]
            f10 = base_colors[x1 * original_size + y0]
            f11 = base_colors[x1 * original_size + y1]
            
            c0 = np.array(colors.to_rgba(f00))
            c1 = np.array(colors.to_rgba(f01))
            c2 = np.array(colors.to_rgba(f10))
            c3 = np.array(colors.to_rgba(f11))
            
            weight_x = x - x0
            weight_y = y - y0
            
            interpolated_color = (
                c0 * (1 - weight_x) * (1 - weight_y) +
                c1 * (1 - weight_x) * weight_y +
                c2 * weight_x * (1 - weight_y) +
                c3 * weight_x * weight_y
            )
            new_colors.append(colors.to_hex(interpolated_color))
    
    return new_colors

# Note: base on public notebook
# Source: https://github.com/mikhailsirenko/bivariate-choropleth/blob/main/bivariate-choropleth.ipynb
def create_bivariate(data, x = 'x', y = 'y', size = 3, palette_name = 'cividis', labels = ('varx','vary')):
    # Add small noise to avoid duplicate bin edges
    data['x'] = data['x'] + np.random.normal(0, 1e-6, len(data))
    data['y'] = data['y'] + np.random.normal(0, 1e-6, len(data))
    
    # Create bins
    var1_lab = [str(i+1) for i in range(size)]
    var2_lab = [chr(i).upper() for i in range(ord('a'),ord('z')+1)][:size]
    
    data['Var1_Class'] = pd.qcut(data['x'], size, labels = var1_lab).astype(str)
    data['Var2_Class'] = pd.qcut(data['y'], size, labels = var2_lab).astype(str)
    data['Bi_Class']   = data['Var1_Class'] + data['Var2_Class']
    data['Bi_Class']   = np.where(data['Var1_Class'] == "nan",np.nan,data['Bi_Class'])
    data['Bi_Class']   = np.where(data['Var2_Class'] == "nan",np.nan,data['Bi_Class'])
    
    # Define colors for matrix legend
    base    = [f"{i}{j}" for i in var1_lab for j in var2_lab]
    palette = color_sets[palette_name]
    
    if len(base) == len(palette):
        # Create color column
        data['Bi_Color'] = data['Bi_Class'].replace(dict(zip(base, palette)))
        all_colors       = palette
    else: 
        # Create color column
        ncolor = expand_colors(palette, size)
        data['Bi_Color'] = data['Bi_Class'].replace(dict(zip(base, ncolor)))
        all_colors       = ncolor  
    
    # Missing values
    data['Bi_Color'] = np.where(data['Bi_Class'].isna(),"#d3d3d3",data['Bi_Color'])
    
    # Map 
    fig, ax = plt.subplots(figsize = (8,8))

    # Step 1: Map
    data.to_crs('EPSG:3857').plot(ax    = ax, 
                                  color = data['Bi_Color'],
                                  categorical = True, 
                                  legend      = False,
                                  linewidth   = 0.1,
                                  edgecolor   = 'black') 
    #ctx.add_basemap(ax = ax, source = ctx.providers.CartoDB.Positron) 
    plt.tight_layout() 
    plt.axis('off') 
    
    # Step 2: Legend
    bbox          = ax.get_position()
    legend_width  = 0.1
    legend_height = 0.1
    legend_x      = bbox.x1 -legend_width - 0.01
    legend_y      = bbox.y0 + 0.04
    
    ax2   = fig.add_axes([legend_x, legend_y, legend_width, legend_height]) 
    alpha = .8
    
    for col in range(size):
        for row in range(size):
            xmin = col / size
            xmax = (col + 1) / size
            ymin = row / size
            ymax = (row + 1) / size
            color_index = col * size + row
            ax2.axvspan(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, alpha=alpha, color=all_colors[color_index])
    
    # Step 3: Legend text
    ax2.tick_params(axis='both', which='both', length=0) # remove ticks from the big box
    ax2.axis('off'); # turn off its axis
    ax2.annotate("", xy=(0, 1), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1, color = "black")) # draw arrow for x 
    ax2.annotate("", xy=(1, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1, color = "black")) # draw arrow for y 
    ax2.text(s=labels[0], x=0.1, y=-0.25, fontsize = 8) # annotate x axis
    ax2.text(s=labels[1], x=-0.25, y=0.1, rotation=90, fontsize = 8); # annotate y axis
    
    plt.show()