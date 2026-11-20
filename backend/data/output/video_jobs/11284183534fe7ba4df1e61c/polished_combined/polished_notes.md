# Study notes

## Artificial intelligence

# Artificial Intelligence Overview

Artificial intelligence (**AI**) is a broad field of computer science that focuses on training computers to perform tasks that humans typically excel at.

## Machine Learning
Machine learning (**ML**) is a key subdomain of AI and consists of two main branches:

1. **Statistical Machine Learning** – Includes classic algorithms such as:
   - `linear regression`
   - `decision tree`
   - `k-means`
   These methods are used for **classification** and **regression** tasks.
2. **Deep Learning** – Centers on **neural networks**. Whenever a new neural network architecture is employed, it falls under deep learning.

### Neural Network Architectures
- **Convolutional Neural Network (CNN)** – A type of neural network designed for processing grid‑like data, especially images.
- **Recurrent Neural Network (RNN)** – Suited for sequential data such as time series or language.
- **Transformer** – A modern neural network architecture that powers contemporary generative AI and agentic AI systems.

---
*All concepts are presented in the order of the original notes, with key terms bolded and technical terms formatted as `inline code` for clarity.*

## regular expression

## Overview of Key Concepts

- **Regular expression**: A fundamental concept in computer science used to define search patterns for strings.
- **Rule‑based system**: A system that operates on explicit, hand‑crafted rules rather than on machine‑learning models.
- **Statistical machine learning**: A subset of machine learning that emphasizes **probabilistic models** to infer patterns from data.
- **Deep learning**: A subfield of machine learning that builds **neural network architectures** to automatically learn hierarchical representations.

## spam classification

# Spam Classification

**Spam classification** is the process of distinguishing unwanted email messages (spam) from legitimate ones. 

- A **human** or **computer program** is trained on thousands of **labeled** spam and non‑spam emails. 
- The training data enables the model to **learn patterns** that differentiate spam from legitimate messages.

This foundational approach underlies most modern email filtering systems.

## inference phase

## Inference Phase

The **inference phase** is the stage where a trained model is applied to new, unseen data to generate predictions or outputs. During this phase, the model utilizes the patterns and knowledge it acquired during training to infer results without further updating its parameters.

- **Purpose**: Deploy the model for real‑world tasks such as classification, regression, translation, or recommendation.
- **Key Steps**:
  1. **Load** the trained model and its weights.
  2. **Preprocess** incoming data to match the format used during training (e.g., scaling, tokenization).
  3. **Run** the model on the preprocessed data using `model.predict()` or an equivalent inference call.
  4. **Post‑process** the raw outputs into a usable form (e.g., converting logits to class labels, applying thresholds).
- **Considerations**:
  - **Latency**: Optimize for speed, especially in real‑time applications.
  - **Batching**: Process multiple inputs together when possible to improve throughput.
  - **Resource Usage**: Choose appropriate hardware (CPU, GPU, TPU) based on model size and performance requirements.

By carefully managing these aspects, the inference phase ensures that the model delivers accurate and efficient predictions in production environments.

## machine learning

## Introduction to Machine Learning

Machine learning is a **discipline within computer science** that focuses on training computers using data so they can make predictions without being explicitly programmed.

### Traditional Programming vs. Machine Learning
- **Traditional software**: Developers write explicit logic to handle every possible case.
- **Machine learning**: Developers provide *input‑output pairs* (training data) and the system discovers the underlying patterns or logic automatically.

### Core Tasks
1. **Classification** – assigning items to discrete categories.
2. **Regression** – predicting a **continuous numeric value** from input features.

These tasks form the foundation of most machine‑learning applications.

## classification

# Machine Learning Fundamentals

## 1. Classification

**Classification** is a supervised learning task where the goal is to assign input instances to one of several predefined categories. Typical examples include spam detection, image recognition, and sentiment analysis.

## 2. Regression

**Regression** involves predicting a continuous numeric value based on input features. Common applications are house‑price estimation, stock‑price forecasting, and temperature prediction.

## 3. Labeled Data

Supervised algorithms such as classification and regression require **labeled data**—datasets where each example is paired with its correct output (a class label or a numeric target). The quality and quantity of these labels directly affect model performance.

## unsupervised learning

# Unsupervised Learning

**Unsupervised learning** is a type of machine learning where the algorithm receives **unlabeled data** and must discover patterns or structures on its own, without explicit guidance.

## Clustering

Clustering is a core technique in unsupervised learning. It groups similar data points together based on their features.

### Outlier Detection

Identifying data points that do **not** belong to any cluster is known as *outlier detection*. Algorithms such as `DBSCAN` are commonly used for this purpose because they can detect clusters of arbitrary shape and label points that lie outside these clusters as outliers.

## Common Programming Language

The programming language most frequently used for AI and machine learning tasks is **Python**. Its extensive libraries (e.g., `scikit-learn`, `TensorFlow`, `PyTorch`) make it ideal for implementing unsupervised learning algorithms.

## structured data

# Structured Data

**Structured data** refers to information that is organized in a predefined format, making it easily searchable and analyzable. It typically follows a consistent schema, such as tables in a relational database or objects in JSON.

- **Key characteristics**:
  - Fixed fields and data types
  - Predictable organization
  - Efficient querying and indexing

*Example*: A table of customer records with columns for `id`, `name`, `email`, and `signup_date`.

## Specialized student detectors for facial features

## how neural networks improve through training

## neural network

# Neural Network

A **neural network** is a computational model inspired by the structure and function of the human brain. It consists of interconnected layers of **neurons** that process data by applying weighted connections and activation functions.

## Core Components
- **Input Layer**: Receives raw data.
- **Hidden Layers**: Perform feature extraction and transformation.
- **Output Layer**: Produces the final prediction or classification.

## How It Works
1. **Data Input** – Raw data is fed into the input layer.
2. **Weighted Sum** – Each neuron computes a weighted sum of its inputs.
3. **Activation** – An `activation function` (e.g., ReLU, sigmoid) introduces non‑linearity.
4. **Propagation** – The result is passed to the next layer.
5. **Training** – The network adjusts weights via **backpropagation** to minimize error.

## Key Concepts
- **Weights**: Parameters that scale input signals.
- **Bias**: An additional parameter that shifts the activation function.
- **Learning Rate**: Controls the step size during weight updates.
- **Epoch**: One full pass through the training dataset.

## Common Architectures
- **Feedforward Neural Network** – Information moves in one direction.
- **Convolutional Neural Network (CNN)** – Specialized for image data.
- **Recurrent Neural Network (RNN)** – Handles sequential data.

Understanding these fundamentals provides a solid foundation for exploring more advanced deep‑learning techniques.

## deep learning

# Deep Learning Overview

**Deep learning** is a *machine learning* technique that employs **neural networks** to learn from large datasets. It requires substantial training samples and mimics the human brain's ability to recognize patterns and make decisions. While powerful, deep learning **does not get everything right all the time**.

### deep learning

## Deep Learning

**Deep learning** is a machine learning technique that employs *neural networks* to learn from large datasets. It requires substantial training samples and mimics the human brain's ability to recognize patterns and make decisions.

## criteria for choosing statistical machine learning versus deep learning

# Types of Neural Network Architectures

Neural networks come in various architectures, each suited to different kinds of data and tasks. Below is an overview of the most common types.

## 1. Feedforward Neural Networks (FNN)
- **Structure**: Layers of neurons arranged in a single direction—from input to output.
- **Use Cases**: Simple classification and regression problems.
- **Key Point**: No cycles; information flows only forward.

## 2. Convolutional Neural Networks (`CNN`)
- **Structure**: Convolutional layers, pooling layers, and fully‑connected layers.
- **Use Cases**: Image recognition, video analysis, and any grid‑like data.
- **Key Concepts**:
  - **Convolution** extracts local features.
  - **Pooling** reduces spatial dimensions while retaining important information.

## 3. Recurrent Neural Networks (`RNN`)
- **Structure**: Connections that form directed cycles, allowing information to persist.
- **Use Cases**: Sequential data such as text, speech, and time series.
- **Variants**:
  1. **Long Short‑Term Memory (`LSTM`)** – mitigates vanishing gradients.
  2. **Gated Recurrent Unit (`GRU`)** – a simpler alternative to `LSTM`.

## 4. Autoencoders
- **Structure**: Encoder network compresses input to a latent representation; decoder reconstructs the original input.
- **Use Cases**: Dimensionality reduction, denoising, and unsupervised feature learning.
- **Key Concept**: The bottleneck forces the model to learn compact, informative features.

## 5. Generative Adversarial Networks (`GAN`)
- **Structure**: Two networks—**generator** and **discriminator**—trained in opposition.
- **Use Cases**: Image synthesis, data augmentation, and style transfer.
- **Key Idea**: The generator creates realistic data while the discriminator learns to distinguish real from fake.

## 6. Transformer Networks
- **Structure**: Stacks of **self‑attention** layers and feedforward sub‑layers.
- **Use Cases**: Natural language processing, translation, and any task requiring long‑range dependencies.
- **Key Concepts**:
  - **Self‑attention** allows each token to weigh the relevance of every other token.
  - **Positional encoding** injects sequence order information.

## 7. Graph Neural Networks (`GNN`)
- **Structure**: Nodes represent entities; edges capture relationships. Message‑passing updates node embeddings.
- **Use Cases**: Social network analysis, molecular property prediction, and recommendation systems.
- **Key Concept**: Exploits the inherent structure of graph‑structured data.

---

Each architecture can be adapted or combined with others to tackle complex problems. Selecting the right type depends on the data modality, task requirements, and computational resources.

## types of neural network architectures

## Deep Learning Frameworks

- **PyTorch** – Developed by Meta. Currently the more popular framework for research and production.
- **TensorFlow** – Developed by Google. Widely used in industry and for large‑scale deployments.

## Transformer Architecture

The **Transformer** architecture is the foundational model for modern generative AI systems, including **GPT‑4**. It enables efficient handling of sequential data through self‑attention mechanisms, making it the backbone of state‑of‑the‑art language models.

## generative AI

## Generative AI

**Generative AI** is a category of artificial intelligence whose primary objective is to **create new content**. This content can include:

- Text
- Audio
- Video
- Images
- Any other form of media

The hallmark of generative AI systems is their ability to produce original outputs that resemble human-created material, enabling applications ranging from creative writing to synthetic media production.

## traditional AI

# Traditional AI

**Traditional AI** refers to the early approaches in artificial intelligence that rely on **explicit rules**, symbolic reasoning, and handcrafted knowledge bases. These systems use `if‑then` logic and predefined algorithms to solve problems, contrasting with modern machine‑learning techniques that learn patterns from data.

## large language model (LLM)

## Generative Language Models

- **Definition**: A type of generative AI that employs massive neural networks trained on extensive text corpora to **predict the next word or sequence of words**.
- **Analogy**: Often likened to a *parrot* that mimics conversations, using statistical probability and randomness to select words. This illustrates how language models operate without genuine comprehension.
- **Mechanism**: The system relies on **statistical probability** and **randomness** to forecast the next token, **without understanding the underlying meaning**.

## Large Language Model (LLM)

- Large Language Model (LLM)
- LLMs use reinforcement learning with human feedback (RLHF) to improve responses and reduce toxic language.

### RLHF

- Reinforcement Learning with Human Feedback, an approach where humans provide feedback to guide the LLM's learning and reduce undesirable outputs.

## Reinforcement Learning with Human Feedback (RLHF)

- RAG combines LLMs with external data sources via APIs, allowing the model to retrieve relevant documents (e.g., HR policies) and use them to answer queries or perform actions.

## tool augmented chatbot

- tool augmented chatbot

## agentic AI system

- agentic AI system
- The characteristic of an agentic AI where a user provides a goal (e.g., onboard a new intern) and the system creates a plan to achieve it.

### AI agent

- An entity that can perceive its environment and act upon it, often by using tools, knowledge, and reasoning.

## low‑code tools

- Tools like n8n, Zapier, and other drag‑and‑drop platforms enable building agentic AI systems without writing code.

## AI agent

- An AI agent has access to tools, knowledge, memory, and an LLM, enabling it to perform autonomous tasks.
- Agentic AI systems combine AI agents with higher autonomy, planning, and multi‑step execution to achieve goals without detailed instructions.
- Generative AI creates new content in response to prompts, such as answering questions with text.
