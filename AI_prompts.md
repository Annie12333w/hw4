# HW 4 — AI Prompt Log

## Problem 2 — Analyze the database

### Prompt records

- **2026-09-28 (setup, scenario):** Perfect - I will start by introducing the scenario, please do not do anything right now. We are going to be creating a real customer website with a helpful chathot for Campus customs. We will be doing this through a react + vite typescript front end and a python fastAPI backend relying on pydanticAI agent. Customers should be able to look at products, create a user account, talk to the chatbot about merch, and see matching items appear on the page. The customer should also get answers about price and stock from a local database. I will provide the database and the product images. We will be using yalebulldogblue.com to develop the style of the website formatting. In the end, we will be pushing the project to a public GITHUB repo.
- **2026-09-28 (setup, data):** @"C:\Users\annie\Downloads\data (2).zip" Please first unzip the contents of this folder into the homework 4 folder. this includes the database and the product images as discussed.
- **2026-09-28 18:28:** Ok we are now starting on Problem 2: Analyze the database. Please take a look at the .db file from the data folder. Could you please list the fields of the table and explain what they are? This should cover catalogue, inventory and users. Please create harness.md (and save it under a folder named Output), write down each table and its fields, and a short description of why the field matters for either the shop or the chatbot.

## Problem 3 — Build the Campus Customs Website

### Prompt records

- **2026-09-28 18:35:** Perfect - We are now working on Problem 3: Build the Campus Customs Website. Please create a front end for campus customs with React + vite +typescript. Please put a nav bar at the top that links to the main pages, home, products, about us, log in and create account (please format with title capitalization). Please use the wording from yalebulldogblue.com for Home and About Us, but please rewrite them in your own voice and do not copy. Next on the products page, please show product images from the catalogue (use the image paths from the database), please then show basic product info (name, price, short description) underneath the photo. Please make each product open a single item page upon clicking the card (large image on one side, full product info on the right side, including full description, price, sizes/stock when you have them). Add a chat interface in the bottom right of the site, it does not need to talk to an agent yet - a stub will call the backend is fine for now. I will need a small API soon to read the database. Please start a simple FastAPI app in backend/main.py to serve products and images.
- **2026-09-28 (follow-up):** Can you help me open it
- **2026-09-28 20:58:** A few notes on the website: Please do not explicitly reference yale bulldog blue on the website. Additionally, when you click on the product card, is it possible to have the product page as an item floating in the middle of the screen with the aforementioned details, and with the existing previous page lightly shaded over in the background? Then have a quick x button to revert back to the previous page.
- **2026-09-28 (follow-up):** Could you also make a more interesting logo for Campus Customs?

## Problem 4 — Create account and login

### Prompt records

- **2026-09-28 21:15:** Thank you - We are now working on Problem 4: Create account and login. We are going to create a flow for both creating accounts (user should provide first name, last name, email, password, and confirm password), and for logging in existing users. New accounts that are successfully created (matching passwords) should go into the users table. The passwords need to be securely stored so that hackers cannot access them, think about using salt and hashing similar to the existing test account. Please connect the database with the page so that you can test the log in and create account functions. Let me know if you have any other suggestions on what I can do to increase security. Please then try the test user (email: test@campuscustoms.yale.edu with password: password) and try creating your own account to test functionality. Then please update harness.md about how the auth works and what is stored for a user and how passwords are protected.
- **2026-09-28 (follow-up):** [screenshot of Create Account card] Could you please fix this formatting so the boxes fit in the card? - Additionally, what is the password to claude.tester@campuscustoms.yale.edu, so that I can test it

## Problem 5 — PydanticAI agent backend

### Prompt records

- **2026-09-28 21:41:** Great we are now working on Problem 5: PydanticAI agent backend. Please build the shop chatbot as a pydanticAI agent behind FastAPI, and connected to the front end chat, please build a backend folder. Please but the API app in backend/main.py, the file ran with Uvicorn.  In main.py create a chat route so a message from the website returns a reply from the agent and anything else I need for products or auth process. Please refer to my homework skills to make sure my AI has access to my portkey_api_key and preferred model version. Please then create a prompts folder (in the backend folder), and within it a prompt.md file where the system prompt will be stored. Next, in the backend folder please create the following: agent.py (agent entry/wiring), tools.py (tools for the agent to call), models.py (pydantic/pydanticAI structured types).  Then please put the campus customes voice and safety basics into prompt.md. Please put start or update types in models.py for chat responses/product cards when needed. In harness.md, please record how the frontend interacts with fastAPI and how the agent is loaded through the prompt file and model Please make sure the backend runs from the folder with the below command: "uvicorn main:app --reload --port 8000"

## Problem 6 — Tools: product info and stock

### Prompt records

- **2026-09-28 21:55:** Great - we are now working on Problem 5: Tools: product info and stock. We are going to give the agent tools in tools.py so that it can look up real information from the database such as product description, price and stock info (including by size when requested). The agent should not invent prices or quantities, and if an item is out of stock, it should say so. Please then expand on  prompt.md so the agent knows how to call these tools. Then add or update return types in models.py. Then update harness.md with each tool created and explain which model fields were chosen for lookup results.
- **2026-09-28 21:56:** apologies, that was problem 6, please make sure thats updated within the ai_prompt file

## Problem 7 — Chat Search That Updates the Page

### Prompt records

- **2026-09-28 22:00:** We are now working on Problem 7: Chat Search That Updates the Page. We are going to add a feature to the site, when the customer asks about a particular type of item, like "what t-shirts do you have available" the agent should search the catalogue and then dynamically update the website so that the matching items appear as product cards, similar to how they are displayed on the products page. This is an API contract, the agent returns structured product matches and then the front end renders them on the website. Make sure that the single-item page built in problem 3 still works upon clicking on the product card and their original location/search results in the page is kept in the background. Make sure that the user can escape their filtered chat results by creating a return to full menu button. Please then update prompt.md and harness.md so it is clear how the search results reach the page.

## Problem 8 — Customer memory

### Prompt records

- **2026-09-28 22:06:** We are now working on Problem 8: Customer memory. When a shopper is logged in, please save their chat history in the database in an appropriate table and reload it upon return. The agent should know who it is talking to, this should be put in agent deps and/or tools that can be called. The agent should also have page context, so that if someone is on a t-shirt product page, and asks "do you have this in red" the agent understands which item they are referencing. Non-logged in users can still talk to the chatbot, but history is not stored. Please document chat history protocol discussed in harness.md and what customer fields the agent sees and how the page context is passed.

## Problem 9 — Usability improvements

### Prompt records

- **2026-09-28 22:17:** Problem 9: Usability improvements. We are going to now work on creating 2 front-end usability improvements and 2 backend usability improvements. I have actually already created multiple front-end usability improvements during the time that I have given these prompts. The first was making the full page item appear as a floating window in the screen so that users can return to their original spot in their scroll and not lose their progress. The second was making a return to full menu item button when the chat initiates a filtered result on the page so that users can retain control of their experience. On the backend, can you please help provide me four options of potential usability improvements I can do to make the agent output faster, more accurate, or cheaper? these could encompass new tools or protocols for the agent. I will then choose 2 out of 4. Afterwards, please implement the backend changes and create usability.md to detail each of the improvements including, what was added and why it helps the shopper or business.
- **2026-09-28 (choice):** Selected backend options: "One-call product snapshot (faster + cheaper)" and "Typo-tolerant search (more accurate)".

## Problem 10 — Style the website

### Prompt records

- **2026-09-28 22:31:** Next we are going to work on Problem 10: style the website. We are going to add creative design so that it feels like a real website. We are going to emulate jpress.com in our website design. Please first set up the menu bar in a similar style, have the campus customs logo in the center with home, products and about us on the left hand side, and the remaining buttons on the right hand side. Also note how the  [jpress.com](https://jpress.com/collections/dress-shirts) displays their products larger (and wider across the page, leaving less white space). Please also make the card borders invisible like it is on the jpress website. I want the website to emulate a quiet luxury fashion site. Next,  I would like you to fetch some images from yalebulldogblue.com where there is a collegiate, youthful environment and feature them on our website to show our brand context and subtly engage our users; please use these photos as banners, zoom as needed but do not stretch any photos. We are not actually going to use this website for anything beyond class purposes so I am not worried about copyright rules for this learning context.
- **2026-09-28 (follow-up):** Please then create design.md (save in the output folder) explain what I've changed in my last prompt and why it would help customers stick around and buy, I have given you a starting point in the last prompt. Please keep it concrete and short.

## Problem 11 — Site testing (app check)

### Prompt records

- **2026-09-28 22:45:** We are now on Problem 11: site testing (app check) Please check the live site and document it in app_check.html (please save this under the output folder). This should be able to be opened with a double click. Please include screenshots and short captions for the following scenarios: 1. chat checking the inventory level of an item (honest stock/price data from the database) 2. dynamic search-result cards appearing after a category question (this is the functionality built in problem 7) and 3. the feature we built where the single-page item opens as a floating window to maintain the previous page in the background. Make sure the HTML is easy to refer to, have a heading for each of the three checks, include a screenshot, and then one or two sentences on what is shown. Please save the screenshot image files to a subfolder within output called app_check_images and link them from app_check.html with relative paths.

## Problem 12 — Audit trail, safety, finish harness

### Prompt records

- **2026-09-28 22:51:** We are now working on Problem 12: Audit trail, safety, finish harness. We are going to create an append only json file called audit_trail.json (saved under output folder) to track agent loop activity (include time, tool name, short args/result, stop reason), please do not wipe it. Could you please also think of some other safety rules to give to the agent and put them in prompts/prompt.md; please let me know what these are. Then we are going to finish harness.md, we are going to talk about the model fields used in models.py and why they were chosen, the tools and abilities used, the safety rules introduced earlier in this prompt, specs (loop limits, result caps, models, how to run the front end and back end).

## Problem 13 — Push to GitHub and submit the URL

### Prompt records

- **2026-09-28 22:55:** [image: expected file layout — hw4/ with AI_prompts.md, requirements.txt, .env.example, .gitignore, README.md, frontend/, backend/ (main.py, agent.py, models.py, tools.py, prompts/prompt.md), output/ (harness.md, design.md, usability.md, app_check.html, app_check_images/, audit_trail.json); local-only data pack data/ (campus_customs.db, products/) not in git] We are now going to work on Problem 13: Push to GitHub and submit the URL. Please put my code in a folder named hw4 and push it to a public github repo (please make sure that it is public) then give me the URL. Please remember to not include my real .env or the data folder (database and product images), Please use .gitignore and include .env.example with placeholders. Please refer to the attached image for context on structuring. the agent is the four files under backend. readme.md should explain how to run the frontend and backend after placing the data pack.
