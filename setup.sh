#!/bin/bash

# Create Streamlit config directory
mkdir -p ~/.streamlit/

# Create config file
echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
\n\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
