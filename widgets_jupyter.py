import ipywidgets as widgets
from IPython.display import display

def choose_continuous_number(callback_function, dropdown_options=None, slider_min=0, slider_max=10, slider_step=1, slider_description="Select Value:", initial_value=None):
    """
    Allows the user to choose a continuous number using either a dropdown
    (if discrete options are provided) or a slider. The selected value is
    passed to the provided callback function.

    Args:
        callback_function (callable): A function that will be called with the
            selected numerical value as its argument.
        dropdown_options (list, optional): A list of discrete numerical options
            to display in a dropdown. If provided, the slider will be disabled.
            Defaults to None.
        slider_min (int or float, optional): The minimum value for the slider.
            Defaults to 0.
        slider_max (int or float, optional): The maximum value for the slider.
            Defaults to 10.
        slider_step (int or float, optional): The step size for the slider.
            Defaults to 1.
        slider_description (str, optional): The description to display next to the slider.
            Defaults to "Select Value:".
        initial_value (int or float, optional): The initial value of the slider
            or the selected value in the dropdown. If None, the slider will
            start at the minimum or the dropdown will have no initial selection.
            Defaults to None.
    """

    if not callable(callback_function):
        raise TypeError("callback_function must be a callable function.")

    if dropdown_options:
        if not all(isinstance(item, (int, float)) for item in dropdown_options):
            raise ValueError("All items in dropdown_options must be numbers.")

        dropdown = widgets.Dropdown(
            options=dropdown_options,
            description="Choose Value:",
            value=initial_value if initial_value in dropdown_options else None,
            disabled=False,
        )

        def on_change(change):
            if change.new is not None:
                callback_function(change.new)

        dropdown.observe(on_change, names='value')
        display(dropdown)

    else:
        slider = widgets.FloatSlider(
            min=slider_min,
            max=slider_max,
            step=slider_step,
            description=slider_description,
            value=initial_value if slider_min <= initial_value <= slider_max and initial_value is not None else slider_min,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.1f'  # Adjust format as needed
        )

        def on_change(change):
            callback_function(change.new)

        slider.observe(on_change, names='value')
        display(slider)

if __name__ == '__main__':
    def process_value(selected_value):
        """
        This is an example of a function that will receive the selected value.
        """
        print(f"Selected value: {selected_value}")
        # You can perform further operations with the selected_value here.

    # Example usage with a slider
    choose_continuous_number(process_value, slider_min=0, slider_max=100, slider_step=0.5, slider_description="Choose a percentage:", initial_value=50.0)

    print("\n--- OR ---\n")

    # Example usage with a dropdown
    discrete_options = [1.0, 2.5, 5.0, 7.5, 10.0]
    choose_continuous_number(process_value, dropdown_options=discrete_options, initial_value=5.0)