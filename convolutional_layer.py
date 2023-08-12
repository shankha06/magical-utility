# Import numpy
import numpy as np

def convolution(input_tensor, kernel_size=3, padding = 0):

    # Define the convoinput_tensorlutional layer parameters
    in_channels = 3 # number of input channels (e.g. RGB image)
    # out_channels = 1 # number of output channels (e.g. number of filters)
    kernel_size = kernel_size # size of the convolutional kernel
    stride = 1 # stride of the convolution
    padding = padding # padding of the input (to preserve the spatial dimensions)

    # Create a random convolutional filter of shape (F, F, Cin, Cout)
    filter = np.random.randint(0,10,size=(kernel_size, kernel_size))

    # Pad the input tensor with zeros
    # input_tensor_padded = np.pad(input_tensor, ((0,0), (padding,padding), (padding,padding), (0,0)))

    # Calculate the output height and width : (W - K +2P)/S + 1
    output_height = (input_tensor.shape[0] - kernel_size + 2 * padding) // stride + 1
    output_width = (input_tensor.shape[1] - kernel_size + 2 * padding) // stride + 1

    print(output_height)

    # Create an empty output tensor of shape (N, H', W', Cout)
    output_tensor = np.zeros((output_height, output_width))

    for h in range(output_height):
        # Loop over the output width dimension
        for w in range(output_width):
            # for c in range(in_channels):
                # Calculate the start and end indices of the input region
                h_start = h * stride
                h_end = h_start + kernel_size
                w_start = w * stride
                w_end = w_start + kernel_size

                # Extract the input region and multiply it element-wise with the filter
                input_region = input_tensor[h_start:h_end, w_start:w_end]
                output_tensor[h, w] = np.sum(input_region * filter[:, :])
    
    return output_tensor

def max_pooling(input_matrix, kernel_size=3, stride=1):
    # Get the shape of the input matrix
    rows, cols = input_matrix.shape

    # Calculate the output shape after max pooling
    output_rows = (rows - kernel_size) // stride + 1
    output_cols = (cols - kernel_size) // stride + 1

    # Create an empty output matrix of the calculated shape
    output_matrix = np.zeros((output_rows, output_cols))

    # Loop over the output rows
    for i in range(output_rows):
        # Loop over the output columns
        for j in range(output_cols):
            # Calculate the start and end indices of the input region
            row_start = i * stride
            row_end = row_start + kernel_size
            col_start = j * stride
            col_end = col_start + kernel_size

            # Extract the input region and apply the max function
            input_region = input_matrix[row_start:row_end, col_start:col_end]
            output_matrix[i, j] = np.max(input_region)

    # Return the output matrix
    return output_matrix

if __name__ == "__main__":
    # Create a dummy input tensor of shape (N, H, W, C)
    # where N is the batch size, H is the height, W is the width and C is the number of channels
    input_tensor = np.random.randint(0,10,size=(32, 32)) # e.g. a batch of 4 RGB images of size 32x32

    output_tensor = convolution(input_tensor)

    # Print the shape of the output tensor
    print(output_tensor.shape) # should be (4, 32, 32, 16)

    output_tensor = max_pooling(output_tensor)

    print(output_tensor.shape) # should be (4, 32, 32, 16)