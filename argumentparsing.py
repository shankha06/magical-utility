import argparse

def parse_inputs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-location', type=str, default='value', help='location of the model')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')

    parser.add_argument('--batch-size', type=int, default=32, help='total batch size for all GPUs')
    parser.add_argument('--epoch', type=int, default=4, help='total number of epochs to be run')
    parser.add_argument('--iterations', type=int, default=4, help='Number of iterations per epoch')

    parser.add_argument('--trigger-evaluation', action='store_true', help='evaluate the models created on benchmark and cross-validation')
    return parser.parse_args()

if __name__ == '__main__':
    options = parse_inputs()
    print(options.batch_size)