import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
from matplotlib.ticker import ScalarFormatter


def alerts_linechart(datapoints):
    fig, ax = plt.subplots(figsize=(datapoints['width'] * 2, datapoints['height'] * 2), dpi=300,
                           facecolor='w')
    y_max = 0
    x_max = 0
    x_max = max(datapoints['values']) if max(datapoints['values']) > x_max else x_max
    y_max = max(datapoints['keys']) if max(datapoints['keys']) > y_max else y_max
    _, = ax.plot(datapoints['values'], datapoints['keys'], '--', linewidth=1,
                 label=datapoints['label'])
    _, = ax.plot(datapoints['values'], datapoints['keys'], 'o', linewidth=1)

    for index, value in enumerate(datapoints['keys']):
        ax.annotate(str(value), xy=(datapoints['values'][index], value + y_max * 0.05))
    ax.legend(loc='lower right')
    ax.set_xlabel(datapoints['x_axis'])
    ax.set_ylabel(datapoints['y_axis'])
    ax.set_title(datapoints['title'])
    plt.xlim(0, x_max + 1)
    plt.ylim(0, y_max + y_max * 0.15)
    ax.grid(True)
    ax.set_xticklabels(
        [str(dp) for dp in datapoints['values']] if not datapoints.get('labels') else datapoints[
            'labels'])
    ax.set_xticks(datapoints['values'])
    fig.savefig(datapoints['path_to_save'], bbox_inches='tight')
    plt.close()


def barchart(datapoints):
    fig, ax = plt.subplots(figsize=(datapoints['width'] * 2, datapoints['height'] * 2), dpi=300,
                           facecolor='w')
    utility_index = datapoints['utility_keys']
    plt.bar(utility_index, datapoints['utility_request'], color='white')
    green_index = datapoints['green_keys']
    plt.bar(green_index, datapoints['green_request'], color='green')
    red_index = datapoints['red_keys']
    plt.bar(red_index, datapoints['red_request'], color='red')
    yellow_index = datapoints['yellow_keys']
    plt.bar(yellow_index, datapoints['yellow_request'], color='orange')
    for index, value in enumerate(datapoints['green_request']):
        ax.annotate(" " + str(value) + " s", xy=(int(datapoints['green_keys'][index])-0.1, value + 0.05), rotation=90,
                    verticalalignment='bottom')
    for index, value in enumerate(datapoints['yellow_request']):
        ax.annotate(str(float(value)*-1) + " s ", xy=(int(datapoints['yellow_keys'][index])-0.1, value - 0.05),
                    rotation=90, verticalalignment='top')
    for index, value in enumerate(datapoints['red_request']):
        ax.annotate(str(float(value)*-1) + " s ", xy=(int(datapoints['red_keys'][index])-0.1, value - 0.05),
                    rotation=90, verticalalignment='top')
    for index, value in enumerate(datapoints['green_request_name']):
        ax.annotate(str(value) + " ", xy=(int(datapoints['green_keys'][index])-0.1, -0.1), rotation=90,
                    verticalalignment='top')
    for index, value in enumerate(datapoints['yellow_request_name']):
        ax.annotate(" " + str(value), xy=(int(datapoints['yellow_keys'][index])-0.1, 0.1), rotation=90,
                    verticalalignment='bottom')
    for index, value in enumerate(datapoints['red_request_name']):
        ax.annotate(" " + str(value), xy=(int(datapoints['red_keys'][index])-0.1, 0.1), rotation=90,
                    verticalalignment='bottom')

    plt.yscale('symlog', basey=2, linthreshy=5.0)
    ax.get_yaxis().set_major_formatter(ScalarFormatter())
    ax.set_frame_on(False)
    ax.axhline(linewidth=1, color='black')
    ax.set_xticklabels([])
    ax.set_xticks([])
    ax.set_yticklabels([])
    ax.set_yticks([])
    fig.savefig(datapoints['path_to_save'], bbox_inches='tight')
    plt.close()
