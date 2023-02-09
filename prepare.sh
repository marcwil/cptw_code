mkdir output_data
mkdir output.pdf
mkdir input_data
cd input_data
wget https://zenodo.org/record/6586185/files/edge_lists_real.zip?download=1 -O networks.zip
unzip networks.zip
rm networks.zip
cd ..

./remove_duplicates.sh
