import amplpy
import csv
import os

import pandas as pd

# one-time-use function to transform data into the .dat format expected by AMPL
def txt_to_dat(base_dir = './BPPLIB/Scholl_CSP_txt',
               target_base_dir = './BPPLIB/Scholl_CSP_dat'):
    
    for folder in ['Scholl_1', 'Scholl_2', 'Scholl_3']:
        folder_path = os.path.join(base_dir, folder)
        target_folder_path = os.path.join(target_base_dir, folder)

        # Create target directory if it doesn't exist
        if not os.path.exists(target_folder_path):
            os.makedirs(target_folder_path)

        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                new_filename = filename.replace('.txt', '.dat')
                target_file_path = os.path.join(target_folder_path, new_filename)

                # Check if the file already exists
                if os.path.exists(target_file_path):
                    print(f"Warning: File '{target_file_path}' already exists. Skipping...")

                with open(os.path.join(folder_path, filename), 'r') as file:
                    lines = file.readlines()

                # Transform the lines
                transformed_lines = [f"param roll_width := {lines[1].strip()};\n", "param: WIDTHS: orders :=\n"]
                transformed_lines += lines[2:]
                transformed_lines[-1] = transformed_lines[-1].strip() + ';'  # Add a semicolon to the last line

                # Write to new .dat file
                with open(target_file_path, 'w') as new_file:
                    new_file.writelines(transformed_lines)

# function to read excel Solutions file into pandas dataframe for use in the script
def solutions_excel_to_df(excel_file_path, filter_selected=True):
    # Read the Excel file
    df = pd.read_excel(excel_file_path)

    # Filter the columns
    df = df[['Name', 'Status', 'Selected', 'Solution']]

    # Filter for only the problems selected for use in the 2016 paper:
    # M. Delorme, M. Iori, and S. Martello. Bin Packing and Cutting Stock Problems: Mathematical Models and Exact Algorithms. European Journal of Operational Research, 255(1):1–20, 2016
    if filter_selected:
        df = df[df['Selected'] == 1]

    # Change .txt extension to .dat in the Name column
    df['Name'] = df['Name'].str.replace('.txt', '.dat')

    return df                                  

# Function to find .dat files spread across multiple child directories (no repeat names please!)
def find_file_in_directories(filename, root_directory):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None  # Return None if the file is not found

def solve_ampl_with_different_datafiles(data_dir_str, data_df, ampl_model_file,
                                        ampl_run_file, output_csv):
    # Create an AMPL environment
    amplpy.add_to_path(r"/Users/gabrielpereira/ampl.macos64")
    ampl = amplpy.AMPL()

    # Prepare a CSV file to store the results
    with open(output_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['DataFile', 'Solution'])  # header

        # Iterate over the data files
        for index, row in data_df.iterrows():
            # Put together path to the .dat file
            # Since the dat files are spread across 3 directories for organisation, we need to look for the .dat file
            # within those 3 directories and then put together the full path.
            dat_file = find_file_in_directories(str(row['Name']), data_dir_str)

            # Reset AMPL object
            ampl.reset()

            # Set the model file
            ampl.read(ampl_model_file)

            # Set the data file to use
            ampl.eval(f'data {dat_file};')

            # "include" (AMPL-equivalent command) the run file
            ampl.read(ampl_run_file)

            # Solve the problem
            ampl.solve()

            # Assuming 'Cut' is the variable of interest (modify as needed)
            cut_values = ampl.getVariable('Cut').getValues().toList()

            # Write the results to CSV
            csvwriter.writerow([dat_file, cut_values])

    # Close the AMPL environment
    ampl.close()


if __name__ == "__main__":
    excel_solutions_path = './BPPLIB/true-solutions/SCHOLL-SOLUTIONS.xlsx'
    dat_folder = './BPPLIB/Scholl_CSP_dat/'
    data_df = solutions_excel_to_df(excel_solutions_path)

    solve_ampl_with_different_datafiles(dat_folder, data_df, 'bpplib.mod', 'bpplib.run', 'test_output.csv')

