
import numpy
from timing import n, starting_delay, ending_delay, message_delays, z_score, \
    sample_means_file_path, standard_errors_file_path, graph_file_path
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Load the results
    sample_means = numpy.loadtxt(fname=sample_means_file_path, dtype='float', delimiter=',')
    standard_errors = numpy.loadtxt(fname=standard_errors_file_path, dtype='float', delimiter=',')

    # Plot the points and their error bars
    thickness = 2
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9))
    ax1.errorbar(message_delays, sample_means[0], yerr=z_score * standard_errors[0],
                 fmt='o', markersize=thickness * 3, capsize=thickness * 2, capthick=thickness,
                 label='End-to-End Delay', linewidth=thickness, color='red')
    ax2.errorbar(message_delays, sample_means[1], yerr=z_score * standard_errors[1],
                 fmt='o', markersize=thickness * 3, capsize=thickness * 2, capthick=thickness,
                 label='In-System Delay', linewidth=thickness, color='blue')

    # Add a horizontal line for 60 ms
    benchmark = 60
    edge_spacing = 15
    ax1.plot([starting_delay + edge_spacing, ending_delay - edge_spacing], [60, 60],
             label='60ms Benchmark', linestyle='--', linewidth=thickness, color='green')
    ax2.plot([starting_delay + edge_spacing, ending_delay - edge_spacing], [60, 60],
             label='60ms Benchmark', linestyle='--', linewidth=thickness, color='green')

    # Set the axis. Reversing the x-axis to show decrease in time
    ax1.axis(xmin=starting_delay + edge_spacing, xmax=ending_delay - edge_spacing, ymin=0)
    ax2.axis(xmin=starting_delay + edge_spacing, xmax=ending_delay - edge_spacing, ymin=0)
    fig.suptitle('Average Response Time for {} Messages'.format(n), fontsize=32)
    ax1.set_title('End-to-End Delay')
    ax2.set_title('In-System Delay')
    ax1.set(xlabel='Time Between Messages (ms)', ylabel='Average Response Time (ms)')
    ax2.set(xlabel='Time Between Messages (ms)', ylabel='Average Response Time (ms)')
    ax1.grid(True, linewidth=1)
    ax2.grid(True, linewidth=1)

    plt.savefig(graph_file_path)
    plt.show()
