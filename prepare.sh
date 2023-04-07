mkdir -p output_data
mkdir -p output.pdf
mkdir -p input_data

cd input_data
wget https://zenodo.org/record/6586185/files/edge_lists_real.zip?download=1 -O networks.zip
unzip networks.zip
rm networks.zip
cd ..

./remove_duplicate.sh

wget http://www.gust.org.pl/projects/e-foundry/latin-modern/download/lm2.004otf.zip
unzip -p lm2.004otf.zip lmroman10-regular.otf > ./plotting/lmroman10-regular.otf
rm lm2.004otf.zip
wget https://www.gust.org.pl/projects/e-foundry/lm-math/download/latinmodern-math-1959.zip 
unzip -p latinmodern-math-1959.zip latinmodern-math-1959/otf/latinmodern-math.otf > ./plotting/latinmodern-math.otf
rm latinmodern-math-1959.zip
