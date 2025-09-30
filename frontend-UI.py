import streamlit as st 

st.title =("Document Upload")

internal_doc  = st.file_uploader("Upload internal files",  accept_multiple_files=True)
for  file  in internal_doc:
        st.write("Uploaded:", file.name)

import  pandas  as pd

if internal_doc:
        content  = internal_doc.read().decode("utf-8")
        st.text(content)

regulation_doc  = st.file_uploader("Upload regulation files",  accept_multiple_files=True)
for  file  in regulation_doc:
        st.write("Uploaded:", file.name)

import  pandas  as pd

if regulation_doc:
        content  = regulation_doc.read().decode("utf-8")
        st.text(content)