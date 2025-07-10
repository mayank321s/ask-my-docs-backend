import openai

openai.api_key = "YOUR_OPENAI_KEY"

def askLlm(question, context_chunks):
    context = "\n".join([chunk["chunk_text"] for chunk in context_chunks])
    prompt = f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {question}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message["content"]