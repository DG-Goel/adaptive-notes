# Study notes

- Artificial intelligence is an overarching field in computer science where we train computers to perform tasks which humans are generally good at.
- Examples of tasks include recognizing patterns, visual capabilities, voice or text capabilities.
- Machine learning is an important subdomain within artificial intelligence.
- Machine learning has two main branches: statistical machine learning and deep learning.
- Statistical machine learning includes algorithms such as linear regression, decision tree, and k-means for tasks like classification and regression.
- Deep learning is mainly about neural networks.
- Neural networks have different architectures such as CNN, RNN, and transformer.
- Transformer architecture is a key reason behind modern generative AI and agentic AI.
- Regular expressions and rule‑based systems are AI‑related components that are not part of machine learning.
- Statistical ML and deep learning are overlapping but distinct concepts.
- Machine learning typically has two phases: training and inference.

## machine learning

- machine learning is a discipline in computer science where we train machines on data so that they can make predictions without explicit programming.
- Traditional software programming takes an input and an equation and produces an output, whereas machine learning takes input‑output pairs and derives the underlying relationship.
- Machine learning is a discipline in computer science where we train machines on data so that they can make predictions without explicit programming.
- In machine learning you do not perform explicit programming; you give input‑output examples and the system discovers the logic or pattern.
- Machine learning tasks are mainly divided into two categories: classification and regression.
- Clustering is a technique that falls under unsupervised machine learning, where patterns are noticed and items are grouped into buckets based on those patterns.
- Unsupervised learning involves providing an unlabeled data set to a machine learning program, which then learns to identify patterns and structures in the data without any explicit guidance.
- Clustering can be used for outlier detection; data points that do not belong to any cluster are marked as outliers.
- Algorithms such as DBSCAN, K-means, and hierarchical clustering are examples of unsupervised machine learning algorithms.
- Structured data (rows and columns) differs from unstructured data (images, text, video) which lack a tabular format and thus present challenges for machine‑learning models.
- you see they are called features okay vendor, amount, location and if you are using statistical machine learning algorithms such as decision tree or xgboost and so on they perform well on
- When features like vendor, amount, and location are defined, statistical ML algorithms (e.g., decision tree, XGBoost) perform well.
- perform well on

## deep learning

- deep learning is a machine learning technique that uses neural networks to learn from large amounts of data
- If you have simple features, such as structured data in tables, you should use statistical machine learning.
- If you have complex features, such as images, videos, or other unstructured data, you should use deep learning.
- Deep learning can also be applied to structured data, even though it is not the default recommendation.
- When you have a huge amount of structured data, some practitioners still use deep learning.
- Choosing between statistical ML and deep learning requires using these loose guidelines and then experimenting to see which approach gives the best performance.
- Unstructured data includes videos, audio, text, and images.
- If you have a huge number of training samples, deep learning will usually perform better.
- A feed forward neural network passes information from input to hidden to output layers without any loops.
- Recurrent neural networks are represented with a time axis to show the sequential processing of inputs.
- Transformer architecture is described as the most important architecture for modern generative AI applications.
- PyTorch (by Meta) and TensorFlow (by Google) are the two main deep‑learning frameworks.
- PyTorch is currently more popular than TensorFlow.
- Generative models can produce text, images, and videos from textual prompts.
- Generative AI is a category of AI where the objective is to generate new content.
- New content can be text, audio, video, anything.
- Traditional AI is used for classification, regression, prediction, and decision making and is considered lightweight.
- Generative AI involves pre‑training on massive datasets such as all internet text and books.
- Traditional AI tooling includes XGBoost and scikit‑learn.
- Generative AI tooling mainly uses large language models (LLMs).
- The modern generative AI revolution is possible because of large language models (LLMs).
- ChatGPT is powered by an LLM called GPT.
- A language model predicts the next set of words based on statistical probability and randomness, similar to a stochastic parrot.
- When the chatbot is given a more complex goal, such as onboarding a new intern, it can perform multi‑step planning and execute actions like creating an onboarding checklist, scheduling a welcome meeting, and sending access requests.
- Agentic AI systems provide the LLM with access to knowledge, memory, and external tools, and use a reasoning model to create a plan and execute the steps.
- Goal‑oriented planning is a characteristic of agentic AI where the user provides a goal (e.g., onboarding a new intern) and the system autonomously decides the sequence of actions to achieve it.
- The terms "AI agent" and "agentic AI" are used interchangeably to describe systems that can perceive the environment and act autonomously.
- AI agents can make decisions and take actions autonomously.
- AI agents can reason through complex tasks, plan multi‑step actions, and execute them without detailed instructions.
- Frameworks such as Auto‑GPT, Google Agent Development Kit, and OpenAI’s toolkit provide Python packages for building AI agents.
- Low‑code/no‑code platforms like n8n, Zapier, and n18 enable building agentic AI systems without writing code.
- An AI agent typically includes a memory store, a chat model (LLM), and tool integrations such as Jira or Slack.
- Agentic AI systems can automate onboarding workflows, creating Jira accounts, ordering laptops, and adding new hires to appropriate Slack channels based on role.
- Agentic AI has higher autonomy than generative AI, performing planning, reasoning, and multi‑step actions.
- Generative AI primarily creates new content (e.g., answering questions) without taking external actions.
- Agentic AI can integrate multiple agents, each with its own tools and memory, to collaborate on tasks.
