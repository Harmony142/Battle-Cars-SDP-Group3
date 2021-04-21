
import numpy
from timing import n, starting_delay, ending_delay, message_delays, sample_means_file_path, standard_errors_file_path
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Load the results
    sample_means = numpy.loadtxt(fname=sample_means_file_path, dtype='float', delimeter=',')
    standard_errors = numpy.loadtxt(fname=standard_errors_file_path, dtype='float', delimeter=',')

    # Plot the points and their error bars
    thickness = 2
    plt.errorbar(message_delays, sample_means - 500, yerr=standard_errors - 330,
                 fmt='o', markersize=thickness * 3, capsize=thickness * 2, capthick=thickness,
                 label='End-to-End Delay', linewidth=thickness, color='red')
    plt.errorbar(message_delays, sample_means - 550, yerr=standard_errors - 335,
                 fmt='o', markersize=thickness * 3, capsize=thickness * 2, capthick=thickness,
                 label='In-System Delay', linewidth=thickness, color='blue')

    # Add a horizontal line for 60 ms
    plt.plot(message_delays, numpy.zeros(len(message_delays)) + 60,
             label='60ms Benchmark', linewidth=thickness, color='green')

    # Set the axis. Reversing the x-axis to show decrease in time
    edge_spacing = 15
    plt.axis(xmin=starting_delay + edge_spacing, xmax=ending_delay - edge_spacing, ymin=0)
    plt.title('Average Response Time for {} Messages'.format(n))
    plt.xlabel('Time Between Messages (ms)')
    plt.ylabel('Average Response Time (ms)')
    plt.grid(True, linewidth=1)
    plt.legend()
    plt.show()
