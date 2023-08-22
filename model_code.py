from transformers import DebertaV3Tokenizer, DebertaV3ForMaskedLM
tokenizer = DebertaV3Tokenizer.from_pretrained('microsoft/deberta-v3-base')
model = DebertaV3ForMaskedLM.from_pretrained('microsoft/deberta-v3-base')


# Input sentence with a mask token and a context
input_sentence = "He is a famous [MASK] player."
context = "He plays for the Indian national team and is known for his batting skills."

# Encode the input sentence and the context
input_ids = tokenizer.encode(input_sentence, context, return_tensors='pt')

# Generate predictions for the mask token
output = model(input_ids)
predictions = output.logits[0, input_ids[0] == tokenizer.mask_token_id]

# Get the top 5 predicted tokens
top_tokens = predictions.topk(5).indices

# Print the predicted tokens and their probabilities
for token in top_tokens:
  word = tokenizer.decode([token])
  prob = predictions[token].exp().item()
  print(f"{word}: {prob:.4f}")
