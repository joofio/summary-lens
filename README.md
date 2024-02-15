# summary-lens

## Usage

needs 3 variables (passed as -e in the docker run stage)
1. OPENAI_KEY for acessing OPENAI
2. SERVER_URL to access data (IPS AND epi)
3. MODEL_URL for localmodels - the URL for ollama (the one supported at this stage)



## Models



1. https://ai.meta.com/blog/5-steps-to-getting-started-with-llama-2/
2. https://huggingface.co/docs/transformers/model_doc/mixtral


## medical

1. https://www.ai-contentlab.com/2023/11/on-use-of-large-language-models-in.html
2. https://github.com/chaoyi-wu/PMC-LLaMA



## prompts Eng.

Creating an effective prompt for a Large Language Model (LLM) to summarize a medical document considering patient characteristics involves a careful blend of specificity, clarity, and context provision. Here's a structured approach to formulating your request:

### **Initial Prompt Design:**

"Please summarize the attached medical document focusing specifically on the implications and findings relevant to a patient with the following characteristics: [insert patient characteristics here, such as age, gender, pre-existing conditions, and any other relevant medical history]. Highlight any treatment recommendations, potential risks, and necessary follow-ups. Ensure the summary is concise and tailored to the patient's profile, providing clear insights into how the document's content applies to their specific situation."

### **Prompt Refinement for Clarity and Specificity:**

1. **Introduction of Patient Characteristics:**
   - Clearly outline the patient's age, gender, and any pertinent medical history that may influence the interpretation of the document. For example, "The patient is a 65-year-old male with a history of diabetes and hypertension."

2. **Objective of the Summary:**
   - Specify that you are seeking a summary that not only condenses the document but also emphasizes information relevant to the patient's care. For instance, "Focus on summarizing treatment options, prognostic factors, and any lifestyle or medication adjustments suggested in the document."

3. **Request for Actionable Insights:**
   - Indicate the need for actionable insights derived from the document, such as specific treatment recommendations or lifestyle changes, tailored to the patient's characteristics. This can be articulated as, "Please provide actionable insights based on the document's content that would directly benefit the patient's management plan."

4. **Format Specification:**
   - If you have a preference for how the summary should be structured (bullet points, a short paragraph, etc.), mention it. For example, "Present the summary in bullet points for clarity and ease of understanding."

### **Refined Prompt Example:**

"Given a medical document attached, I request a summary focused on the aspects most relevant to a 65-year-old male patient with diabetes and hypertension. Please highlight key findings, treatment recommendations, and any mentions of lifestyle or medication adjustments pertinent to his conditions. Aim for a concise summary that provides clear, actionable insights tailored to his specific health profile, presented in bullet points for easy reference."

### **Considerations:**

- **Patient Privacy:** Ensure that any personal information shared respects privacy laws and regulations, avoiding excessive detail that could compromise patient confidentiality.
- **Accuracy and Comprehensibility:** The LLM's ability to understand and process medical documents depends on the clarity of the prompt and the document's complexity. Ensure the document is well-structured and the prompt is precisely formulated to improve the quality of the summary.

This approach ensures that your request to the LLM is clear, specific, and structured to yield a summary that is directly relevant and actionable for the patient in question.