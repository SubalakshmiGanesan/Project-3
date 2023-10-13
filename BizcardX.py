# Import the modules

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import sqlite3
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re
from streamlit_extras.add_vertical_space import add_vertical_space

# Setting the page configuration

icon = Image.open("Images/icon.jpg")
st.set_page_config(page_title="BizCardX-Extracting Business Card Data with OCR", page_icon=icon, layout="wide",initial_sidebar_state = 'expanded',menu_items = {'About':"""# Thsi OCR app is created by *Subalakshmi Ganesan*!"""})
st.markdown("<h1 style = 'text-align:center; color:blue;'>BizCardX: Extracting Business Card Data with OCR</h1>",unsafe_allow_html = True)

st.write('-----')
st.sidebar.header(":wave: :blue[**Hello! Welcome to the dashboard**]")
with st.sidebar:
        selected = option_menu("Menu", ["Home","Upload & Extract","Modify"], 
        icons=["house","cloud-upload","pencil-square"],
        menu_icon= "menu-button-wide",
        default_index=0,
        styles={"nav-link": {"font-size": "15px", "text-align": "left", "margin": "-1px", "--hover-color": "#3639ad"},
                        "nav-link-selected": {"background-color": "#3639ad"}})

        
# Initializing the EasyOCR Reader
reader = easyocr.Reader(['en'])


# Connecting with sql database
connection = sqlite3.connect("BizcardX.db")
curs = connection.cursor()


#Table creation
query = """CREATE TABLE IF NOT EXISTS Card_data
        (Company_Name TEXT,
        Card_Holder TEXT,
        Designation TEXT,
        Mobile_Number VARCHAR(40),
        Email TEXT,
        Website TEXT,
        Area TEXT,
        City TEXT,
        State TEXT,
        Pincode VARCHAR(10),
        Image LONGBLOB)"""

curs.execute(query)


#Upload & Extract menu

if selected == "Upload & Extract":
    st.subheader(":violet[**You can view the Database Here**]")
    add_vertical_space(1)
    if st.button(":blue[**Show the Stored Database**]"):
        query1 = """SELECT * from Card_data"""
        curs.execute(query1)
        db_df = pd.DataFrame(curs.fetchall(),columns = ['Company Name','Card Holder','Designation','Mobile Number','Email','Website','Area','City','State','Pincode'])
        add_vertical_space(1)
        st.write(db_df)
    
    add_vertical_space(3)
    st.subheader(":violet[**Please Upload your Business Card**]")
    add_vertical_space(2)
    upload = st.file_uploader("**Upload Here**", label_visibility = 'collapsed',type=['png','jpeg','jpg'])
    add_vertical_space(2)
   
    if upload is not None:
        
        def save_card(upload):
            uploads_dir = os.path.join(os.getcwd(),"Uploaded Cards")
            with open(os.path.join(uploads_dir,upload.name),"wb")as f:
                f.write(upload.getbuffer())
                
        save_card(upload)
        
        
        def image_preview(image,res):
            for (bbox,text,prob) in res:
                #to unpack the bounding box
                (tl,tr,br,bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image,tl,br,(0,255,0),2)
                cv2.putText(image,text,(tl[0],tl[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0),2)
                
            plt.rcParams['figure.figsize'] = (15,15)
            plt.axis('off')
            plt.imshow(image)
            
            
       #Displaying the uploaded card
        col1,col2 = st.columns(2,gap = 'large')
        with col1:
            st.markdown("### :violet[You have uploaded the card]")
            st.image(upload)
            
       # Displaying the card with highlights
        with col2:
            with st.spinner("Please wait processing image..."):
                st.set_option("deprecation.showPyplotGlobalUse",False)
                saved_img = os.getcwd() + "\\" + "Uploaded Cards" + "\\" + upload.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### :violet[Image Processed and Data Extracted]")
                st.pyplot(image_preview(image,res))
                
        add_vertical_space(1)           
        # EasyOCR
        saved_img = os.getcwd() + "\\" + "Uploaded Cards" + "\\" + upload.name
        result = reader.readtext(saved_img,detail = 0,paragraph = False)
        
        
        
        # Converting the Image to Bianry to Upload into SQl Database
        def img_to_bin(file):
            with open(file,'rb')as file:
                binaryData = file.read()
            return binaryData
        
        
        data = {"company_name" : [],
                "card_holder" : [],
                "designation" : [],
                "mobile_number":[],
                "email" : [],
                "website" :[],
                "area" : [],
                "city" : [],
                "state" : [],
                "pincode" : [],
                "image" : img_to_bin(saved_img)
               }
        
        def get_data(res):
            for ind, i in enumerate(res):

                # To get WEBSITE_URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] + "." + res[5]

                # To get EMAIL ID
                elif "@" in i:
                    data["email"].append(i)

                # To get MOBILE NUMBER
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # To get COMPANY NAME
                elif ind == len(res) - 1:
                    data["company_name"].append(i)

                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)

                # To get PINCODE
                if len(i) >= 6 and i.isdigit():
                    data["pincode"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pincode"].append(i[10:])
        
        get_data(result)
        
        
        
        #To create a dataframe
        df = pd.DataFrame(data)
        st.success("### Data Extracted...!")
        st.write(df)
        
        
    # Dataframe uploaded to database
    if st.button(":blue[**Upload to Database**]"):
        df.to_sql("Card_data",connection,if_exists='append',index = 1)    
        st.success("#### Card details uploaded to database successfully...!")
     
    add_vertical_space(2)
    
    
    # to view the latest updated data
    st.subheader(":violet[You can view the latest updated data here]")
    if st.button(":blue[**View updated data**]"):
        try:
            query_show = """SELECT * FROM Card_data"""
            curs.execute(query_show)
            updated = pd.DataFrame(curs.fetchall(),columns = ['Company Name','Card Holder','Designation','Mobile Number','Email','Website','Area','City','State','Pincode','Image'])
            add_vertical_space(1)
            st.write(updated)
            
        except:
            st.warning("There is no data in the database")
                

            
#Modify Menu
if selected == "Modify":
    st.subheader(":violet[In this Page you can View,Alter and Delete the data from the database]")
    select = option_menu(None,
                         options=["VIEW","ALTER", "DELETE"],
                         default_index=0,
                         orientation="horizontal",
                         styles={"container": {"width": "100%"},
                                 "nav-link": {"font-size": "20px", "text-align": "center", "margin": "-2px"},
                                 "nav-link-selected": {"background-color": "#3639ad"}})
    
    
    
    #Function for view menu
    if select == "VIEW":
            st.subheader(":blue[BizCardX Database]")
            query_show = """SELECT * FROM Card_data"""
            curs.execute(query_show)
            updated = pd.DataFrame(curs.fetchall(),columns = ['Company Name','Card Holder','Designation','Mobile Number','Email','Website','Area','City','State','Pincode','Image'])
            add_vertical_space(1)
            st.write(updated)
            
        
    
    #Function of ALTER menu
    if select == "ALTER":
        st.subheader(":violet[**Please Select the Card Holder Name to Modify**]")
        holder = """SELECT Card_Holder from Card_data"""
        curs.execute(holder)
        result = curs.fetchall()
        business_cards = {}
        for i in result:
            business_cards[i[0]] = i[0]
        options =["None"] + list(business_cards.keys())
        selected_card = st.selectbox("**Select a card**",options)
        if selected_card == "None":
            st.write("#### No card Selected")
        else:
            st.markdown("#### :violet[Update or Modify any data below]")
            curs.execute("SELECT Company_Name,Card_Holder,Designation,Mobile_Number,Email,Website,Area,City,State,Pincode from Card_data WHERE Card_Holder = ?", (selected_card,))
            result = curs.fetchone()
              
                
            #Displaying all the information to modify
            company = st.text_input("Company_Name",result[0])
            holder = st.text_input("Card_Holder",result[1])
            des = st.text_input("Designation",result[2])
            mobile = st.text_input("Mobile Number",result[3])
            email = st.text_input("Email",result[4])
            web = st.text_input("Website",result[5])
            area = st.text_input("Area",result[6])
            city = st.text_input("City",result[7])
            state = st.text_input("State",result[8])
            pin = st.text_input("Pincode",result[9])
            
            add_vertical_space(1)
            
            
            #Update the whole information to the database
            if st.button(":blue[**Commit Changes to DB**]"):
                curs.execute("UPDATE Card_data SET Company_Name = ?,Card_Holder = ?,Designation = ?,Mobile_Number = ?,Email = ?,Website = ?,Area = ?,City = ?,State = ?,Pincode = ? WHERE Card_Holder = ?",(company,holder,des,mobile,email,web,area,city,state,pin,selected_card))
                connection.commit()
                st.success("#### Information updated in database successfully")
        
           
            
    #Function for Delete menu       
    if select == "DELETE":
        st.subheader(":violet[**Please select the Card to delete**]")
        holder = """SELECT Card_Holder from Card_data"""
        curs.execute(holder)
        result = curs.fetchall()
        business_cards = {}
        for i in result:
            business_cards[i[0]] = i[0]
        options =["None"] + list(business_cards.keys())
        selected_card = st.selectbox("**Select a card**",options)
        if selected_card == "None":
            st.write("#### No card Selected")
        else:
            st.write(f"### You have selected :red[**{selected_card}'s**] data to delete")
            st.write("#### Proceed to delete this card?")
            col1,col2 = st.columns(2)
            with col1:
                if st.button(":blue[**YES**]"):
                    curs.execute("DELETE FROM Card_data WHERE Card_Holder = ?", (selected_card,))
                    connection.commit()
                    st.success("#### Business card information successfully deleted from the database")
            with col2:
                table = st.button(":blue[**NO**]")
            if table:
                st.success("#### You are cancelling your request") 

                
#Home Menu
if selected == "Home":
    col1 , col2 = st.columns(2)
    with col1:
        st.image(Image.open("Images/biz.jpeg"),width=500)
        
    with col2:
        st.write("## :blue[**About :**] Bizcard is a Python application designed to extract information from business cards.")
        st.markdown("## :blue[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
        
    add_vertical_space(2)   
    st.subheader(":blue[**Problem Statement**]")
    st.markdown("1. To develop a streamlit application that allows users to upload an image of business card and extracted relevant information")
    st.markdown("2. Extracted information be displayed in an organized manner in the application's GUI")
    st.markdown("3. The user should be able to easily add it to database with the click of button")
    st.markdown("4. Also allow the user to read,update and also delete the data through streamlit UI")
    add_vertical_space(2)
    st.subheader(":blue[**Approaches**]")
    st.markdown("1. Install the required packages")
    st.markdown("2. Design the user interface")
    st.markdown("3. Implement the image processing and OCR")
    st.markdown("4. Display the extracted information")
    st.markdown("5. Implement database integration")
    st.markdown("6. Test the application")
    st.markdown("7. Improving the application")
    add_vertical_space(2)
    st.subheader(":blue[DataSet]")
    st.markdown("[Click here to open the dataset](https://drive.google.com/drive/folders/1FhLOdeeQ4Bfz48JAfHrU_VXvNTRgajhp)")
    
                 