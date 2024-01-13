import amplpy
import csv
import os
import sys

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

# function to read excel SCHOLL-SOLUTIONS file into pandas dataframe for use in the script
def scholl_solutions_to_df(excel_file_path, filter_selected=True):
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

    # Remove rows where 'Name' starts with 'HARD'
    # These are prohibitively costly to solve.
    df = df[~df['Name'].str.startswith('HARD')]

    # Randomly select 120 rows where 3rd character in 'Name' is 'C'
    # I PROPOSE TO DO 120 OF THESE FOR THE FINAL WORK
    c_rows = df[df['Name'].str[2] == 'C'].sample(n=180, random_state=1)

    # Randomly select 20 rows where 3rd character in 'Name' is 'W'
    # I PROPOSE TO DO 20 OF THESE FOR THE FINAL WORK
    w_rows = df[df['Name'].str[2] == 'W'].sample(n=0, random_state=1)

    # Combine the two filtered DataFrames
    df = pd.concat([c_rows, w_rows])

    return df

# Function to find .dat files spread across multiple child directories (no repeat names please!)
def find_file_in_directories(filename, root_directory):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None  # Return None if the file is not found

# for output redirection (START)
def start_redirection(file_path):
    # Open the file where you want to redirect the output
    sys.stdout = open(file_path, 'a')

# for output redirection (REVERSION to stdout stream)
def stop_redirection():
    # Close the redirection file and revert stdout to its original state
    #sys.stdout.close()
    sys.stdout = sys.__stdout__

def solve_ampl_with_different_datafiles(data_dir_str, data_df, ampl_model_file,
                                        ampl_run_file, output_csv, log_file_path):
    # Create an AMPL environment
    amplpy.add_to_path(r"/Users/gabrielpereira/ampl.macos64")
    ampl = amplpy.AMPL()

    # Set time limit for solution here
    ampl.setOption('cplex_options', 'timelimit=10')

    # Clear contents of current AMPL output log file, if any.
    with open(log_file_path, 'w'):
        pass

    # Prepare a CSV file to store the results
    with open(output_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['DataFile', 'ObjectiveValue'])  # header

        # Iterate over the data files
        for index, row in data_df.iterrows():
            # Put together path to the .dat file
            # Since the dat files are spread across 3 directories for organisation, we need to look for the .dat file
            # within those 3 directories and then put together the full path.
            dat_file = find_file_in_directories(str(row['Name']), data_dir_str)

            stop_redirection()
            print('-------------------------------------------------------------------------')
            print(f'SOLVING PROBLEM NO. {index}')
            os.system(f'say "{str(index)}"')
            print()

            # Append AMPL output to log file
            start_redirection(log_file_path)

            # Reset AMPL object
            ampl.reset()

            # Set the model file
            ampl.read(ampl_model_file)

            # Set the data file to use
            ampl.eval(f'data {dat_file};')

            # "include" (AMPL-equivalent command) the run file
            ampl.read(ampl_run_file)

            # Solve the problem
            try:
                ampl.solve()
                # Extract variables/objective values of interest for storage
                # cut_values   = ampl.getVariable('Cut').getValues().toList()
                # cut_patterns_df = ampl.getParameter('nbr').getValues().toPandas() # take to df
                
                objective_function = ampl.getObjective('Number')
                objective_value = objective_function.value()

                # Write the results to CSV
                csvwriter.writerow([dat_file, objective_value])
            except RuntimeError as e: # If solver takes too long in some particular problem
                print("Solver did not finish within the time limit.")


    # Close the AMPL environment
    ampl.close()


if __name__ == "__main__":
    excel_solutions_path = './BPPLIB/true-solutions/SCHOLL-SOLUTIONS.xlsx'
    dat_folder = './BPPLIB/Scholl_CSP_dat/'
    data_df = scholl_solutions_to_df(excel_solutions_path)

    output_file_name = 'scholl-1-output.csv'
    confirmation = input(f'Confirm the output file name {output_file_name}, i.e., enter it here: ')
    if confirmation == output_file_name:
        solve_ampl_with_different_datafiles(dat_folder, data_df, 'bpplib.mod', 'bpplib.run', output_file_name, './ampl_run_log.txt')
    else:
        print('Wrong name given! Interrupted.')
