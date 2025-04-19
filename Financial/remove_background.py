from PIL import Image, ImageDraw
import os

def create_transparent_logo():
    """
    Crea una versione del logo con sfondo completamente trasparente
    """
    # Percorso dell'immagine originale
    input_path = 'attached_assets/EDED3068-529E-4063-A554-4F34AC77A96F.png'
    # Percorso dell'immagine di output
    output_path = 'assets/logo.png'
    
    # Crea directory assets se non esiste
    os.makedirs('assets', exist_ok=True)
    
    # Apri l'immagine originale
    img = Image.open(input_path)
    img = img.convert("RGBA")
    
    # Ottieni i dati dei pixel
    data = img.getdata()
    new_data = []
    
    # Valori utilizzati per determinare cosa è sfondo e cosa no
    # Definiamo alcune soglie molto specifiche per il nostro caso
    
    for item in data:
        r, g, b, a = item
        
        # Identifica cosa tenere e cosa rendere trasparente
        
        # Mantieni le banconote (verde)
        is_banknote = ((r < 150 and g > 150 and b < 150) or  # Verde scuro
                      (r > 50 and r < 180 and g > 150 and b > 50 and b < 180 and g > r and g > b))  # Verde medio
        
        # Mantieni le monete (oro/giallo)
        is_coin = (r > 200 and g > 150 and b < 120 and r > b)
        
        # Mantieni il testo (scuro)
        is_text = (r < 80 and g < 80 and b < 80)
        
        # Tutto il resto diventa trasparente
        if is_banknote or is_coin or is_text:
            new_data.append(item)  # Mantieni colore originale con piena opacità
        else:
            new_data.append((255, 255, 255, 0))  # Trasparente
    
    # Applica i dati modificati all'immagine
    img.putdata(new_data)
    
    # Rimuovi eventuali bordi trasparenti eccessivi
    # Trova i bordi dell'immagine non trasparente
    alpha = img.getchannel('A')
    bbox = alpha.getbbox()
    
    if bbox:
        # Aggiungi un piccolo margine intorno all'immagine ritagliata
        padding = 5
        width, height = img.size
        # Assicurati che il padding non vada oltre i limiti dell'immagine
        bbox_with_padding = (
            max(0, bbox[0] - padding),
            max(0, bbox[1] - padding),
            min(width, bbox[2] + padding),
            min(height, bbox[3] + padding)
        )
        # Ritaglia l'immagine
        img = img.crop(bbox_with_padding)
    
    # Salva l'immagine con sfondo trasparente
    img.save(output_path, "PNG")
    
    print(f"Logo modificato salvato in {output_path}")
    return output_path

if __name__ == "__main__":
    create_transparent_logo()