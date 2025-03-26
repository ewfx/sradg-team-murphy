# 🚀 Smarter Reconciliation Anomaly Detection with GenAI - Team Murphy

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
- Reconcilers spend huge time and effort in reconciling transaction discrepancies
- Most of the effort goes into identifying anomalies based on historical patterns, recording them and resolving them
- Every anomaly may need a different resolution

  Solution is to detect anomalies and decide on the action to be taken autonomously using GenAI and AI Agents


## 🎥 Demo
🔗 [Live Demo](#) (if applicable)  
📹 [Video Demo](#) (if applicable)  
🖼️ Screenshots:

![Screenshot 1](link-to-image)

## 💡 Inspiration
What inspired you to create this project? Describe the problem you're solving.

## ⚙️ What It Does
- Highly configurable with addition of new reconciliation systems with varying data structures with REST APIs and UX
- Agentic AI with LangGraph provides autonomous agents and flexibility to switch models
- Leveraging RAG provides capabilities to send additional data for reasoning
- Tool calling capabilities leveraged for action decisioning based on external data


## 🛠️ How We Built It
- Python
- Flask
- LangGraph
- OpenRouter
- SQLiteDB
- Bootstrap, jQuery


## 🚧 Challenges We Faced
We tried training an ML model using Classification models like Random Forest and XG Boost and also a couple of unsupervised models like Isolation Forest and Autoencoders. We had done Feature Engineering and decided to use Mean and Std Deviation of the balance columns to train the model and predict anomalies. However, because of lack of a good quality dataset, training the ML model became a challenge. Hence we decided to go with LLM with Prompt Engineering for anomaly detection.

With LLM, we tried finetuning using peft anf LoRA. However, due to lack of computing resources we decided to use the open source pretrained/foundation models. We used OpenRouter to access various models for this.

Providing the right prompt for anomaly detection and prompts for the LLM to decide on the action to be taken was another challenge.

## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone https://github.com/your-repo.git
   ```
2. Install dependencies  
   ```sh
   pip install -r requirements.txt
   ```
3. Run the project  
   ```sh
   cd code/src/py
   python workflow_openrouter_tools.py
   ```

## 🏗️ Tech Stack
- 🔹 Frontend: Bootstrap, jQuery
- 🔹 Backend: Python, Flask, LangGraph, OpenRouter
- 🔹 Database: SQLiteDB
- 🔹 LLM: Open source LLama3, Mistral

## 👥 Team
- **Muralidharan Balanandan** - [GitHub](https://github.com/muralidharan-rade/) | [LinkedIn](https://www.linkedin.com/in/muralidharan-balanandan/)
- **Rajagopalan Krishnamoorthy** - [GitHub](#) | [LinkedIn](#)
- **Madhan Kumar B** - [GitHub](#) | [LinkedIn](#)
- **Sathyendran A** - [GitHub](#) | [LinkedIn](#)
- **Prakash G** - [GitHub](#) | [LinkedIn](#)
