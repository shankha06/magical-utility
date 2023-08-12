# Import torch, torch.nn and torch.optim
import torch
import torch.nn as nn
import torch.optim as optim

# Define the input size, hidden size, output size and learning rate
input_size = 10 # e.g. number of features
hidden_size = 5 # e.g. number of hidden units
output_size = 1 # e.g. number of classes
lr = 0.01 # e.g. learning rate

# Create a simple neural network class that inherits from nn.Module
class SimpleNN(nn.Module):
    # Define the constructor
    def __init__(self, input_size, hidden_size, output_size):
        # Call the parent constructor
        super(SimpleNN, self).__init__()

        # Define the hidden layer with input size and hidden size
        self.hidden_layer = nn.Linear(input_size, hidden_size)

        # Define the ReLU activation function for the hidden layer
        self.relu = nn.ReLU()

        # Define the output layer with hidden size and output size
        self.output_layer = nn.Linear(hidden_size, output_size)

        # Define the sigmoid activation function for the output layer
        self.sigmoid = nn.Sigmoid()

    # Define the forward pass method
    def forward(self, x):
        # Pass the input through the hidden layer and apply ReLU
        x = self.hidden_layer(x)
        x = self.relu(x)

        # Pass the output of the hidden layer through the output layer and apply sigmoid
        x = self.output_layer(x)
        x = self.sigmoid(x)

        # Return the output
        return x

# Create an instance of the simple neural network with the given sizes
model = SimpleNN(input_size, hidden_size, output_size)

# Print the model summary
print(model)

# Define the binary cross entropy loss function
criterion = nn.BCELoss()

# Define the stochastic gradient descent optimizer with the given learning rate
optimizer = optim.SGD(model.parameters(), lr=lr)

# Define some dummy input and target data for demonstration purpose
x = torch.randn(4, input_size) # e.g. 4 samples with 10 features each
y = torch.tensor([0, 1, 1, 0]).float().view(-1, 1) # e.g. 4 labels (0 or 1) in one column

# Perform one iteration of forward pass and backward pass
# Forward pass: compute the output and the loss
output = model(x)
loss = criterion(output, y)

# Backward pass: compute the gradients and update the weights
optimizer.zero_grad() # clear any previous gradients
loss.backward() # compute the gradients with backpropagation
optimizer.step() # update the weights with gradient descent

# Print the loss value
print(loss.item())
