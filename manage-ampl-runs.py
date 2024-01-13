import amplpy
import csv
import os

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

def solve_ampl_with_different_datafiles(dat_files, ampl_model_file, ampl_run_file, output_csv):
    # Create an AMPL environment
    amplpy.add_to_path(r"/Users/gabrielpereira/ampl.macos64")
    ampl = amplpy.AMPL()

    # Set the model file
    ampl.read(ampl_model_file)

    # Prepare a CSV file to store the results
    with open(output_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['DataFile', 'Solution'])  # header

        # Iterate over the data files
        for dat_file in dat_files:
            # Read the data file
            ampl.readData(dat_file)

            # Include the run file
            ampl.include(ampl_run_file)

            # Solve the problem
            ampl.solve()

            # Assuming 'Cut' is the variable of interest (modify as needed)
            cut_values = ampl.getVariable('Cut').getValues().toList()

            # Write the results to CSV
            csvwriter.writerow([dat_file, cut_values])

    # Close the AMPL environment
    ampl.close()

if __name__ == "__main__":
    txt_to_dat()