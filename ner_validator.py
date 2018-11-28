import ner

tagger = ner.SocketNER(host='localhost', port=9191)

print tagger.get_entities("No es lo mismo la magia negra que la magia de la negra")
