# Study notes

# Artificial Intelligence Overview

Artificial intelligence (**AI**) is a broad field in computer science that focuses on training computers to perform tasks that humans excel at, such as pattern recognition, visual perception, and voice or text processing.

## Machine Learning

Machine learning (**ML**) is a core subdomain of AI. It is generally divided into two main branches:

1. **Statistical Machine Learning**
   - Includes algorithms like `linear regression`, `decision tree`, and `k-means`.
   - Used for tasks such as **classification** and **regression**.
2. **Deep Learning**
   - Centers on **neural networks**.
   - Common architectures: `CNN` (Convolutional Neural Network), `RNN` (Recurrent Neural Network), and `Transformer`.
   - The **Transformer** architecture underpins modern generative AI and agentic AI.

> **Note:** While statistical ML and deep learning overlap in practice, they remain distinct concepts.

## Machine Learning Workflow

ML typically proceeds through two phases:

1. **Training** – the model learns patterns from data.
2. **Inference** – the trained model makes predictions on new data.

## Non‑ML AI Components

- **Regular expressions** and **rule‑based systems** are AI‑related tools but are not considered part of machine learning.

---

*All key concepts are highlighted in **bold**, and technical terms are shown in `inline code` for clarity.*

## machine learning

# Introduction to Machine Learning

Machine learning is a **discipline in computer science** that trains machines on data so they can make predictions without explicit programming.

## Traditional vs. Machine‑Learning Approaches
- **Traditional software**: takes an input and an explicit equation, then produces an output.
- **Machine learning**: receives *input‑output pairs* and derives the underlying relationship automatically.

## Core Concepts
- **No explicit programming**: you provide examples, and the system discovers the logic or pattern.
- **Tasks** are mainly divided into:
  1. **Classification** – assigning items to predefined categories.
  2. **Regression** – predicting continuous values.

## Unsupervised Learning
- Involves feeding an **unlabeled data set** to the algorithm, which then identifies patterns and structures without guidance.
- **Clustering** is a key unsupervised technique:
  - Groups items into buckets based on similarity.
  - Can be used for **outlier detection** (points that do not belong to any cluster are marked as outliers).
  - Common algorithms: `DBSCAN`, `K-means`, and hierarchical clustering.

## Data Types
- **Structured data**: organized in rows and columns (e.g., spreadsheets, databases).
- **Unstructured data**: lacks a tabular format, such as images, text, and video, posing additional challenges for models.

## Features and Algorithms
- When features like **vendor**, **amount**, and **location** are defined, statistical machine‑learning algorithms perform well, e.g.:
  - `Decision Tree`
  - `XGBoost`

---

## deep learning

# Overview of Machine Learning Approaches

## 1. Choosing Between Statistical ML and Deep Learning
- **Statistical machine learning** is best for *simple, structured features* (e.g., tabular data). Common tools: `XGBoost`, `scikit-learn`.
- **Deep learning** excels with *complex, unstructured features* such as **images**, **videos**, **audio**, and **text**. It can also be applied to large‑scale structured data, though this is not the default recommendation.
- **Guideline:** If you have a **huge number of training samples**, deep learning usually outperforms statistical methods. Ultimately, experiment to determine which approach yields the best performance.

## 2. Types of Data
- **Unstructured data:** videos, audio, text, images.
- **Structured data:** tables, relational databases.

# Deep Learning Fundamentals

## 1. Core Architectures
- **Feed‑forward neural network:** information flows from input → hidden → output layers without loops.
- **Recurrent neural network (RNN):** includes a **time axis** to process sequences sequentially.
- **Transformer:** the dominant architecture for modern **generative AI** applications.

## 2. Frameworks
- **PyTorch** (Meta) – currently the more popular deep‑learning library.
- **TensorFlow** (Google).

# Generative AI vs. Traditional AI

## 1. Traditional AI
- Tasks: classification, regression, prediction, decision‑making.
- Considered **lightweight**.
- Tooling: `XGBoost`, `scikit-learn`.

## 2. Generative AI
- Objective: **generate new content** (text, audio, video, images) from prompts.
- Relies on **large language models (LLMs)** trained on massive datasets (e.g., the entire internet).
- Example: **ChatGPT**, powered by the **GPT** LLM.
- A language model predicts the next words based on statistical probability and randomness – often described as a *stochastic parrot*.

# Agentic AI

## 1. Definition
- **AI agents** (or *agentic AI*) perceive their environment and act autonomously.
- They combine an LLM with **memory**, **knowledge bases**, and **external tools**.
- A **reasoning model** creates a plan and executes multi‑step actions.

## 2. Capabilities
- **Goal‑oriented planning:** given a goal (e.g., onboarding a new intern), the system decides the sequence of actions—creating checklists, scheduling meetings, sending access requests.
- **Autonomy:** can reason, plan, and act without detailed step‑by‑step instructions.
- **Integration:** multiple agents, each with its own tools and memory, can collaborate.

## 3. Components of an AI Agent
1. **Memory store** – retains context across interactions.
2. **Chat model (LLM)** – provides natural‑language understanding and generation.
3. **Tool integrations** – e.g., Jira, Slack, APIs.

## 4. Tooling & Platforms
- **Python libraries:** Auto‑GPT, Google Agent Development Kit, OpenAI’s toolkit.
- **Low‑code/no‑code platforms:** n8n, Zapier, n18 – enable building agentic systems without coding.

## 5. Comparison with Generative AI
- **Generative AI:** creates content (answers, images) but does **not** perform external actions.
- **Agentic AI:** higher autonomy; performs planning, reasoning, and executes multi‑step workflows (e.g., automating onboarding, provisioning accounts, updating Slack channels).

