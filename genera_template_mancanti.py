"""
Genera tutti i template HTML mancanti
"""

import os

BASE = 'core/templates'

# Template da creare
templates = {
    # DOCENTI
    f'{BASE}/anagrafiche/docente_list.html': '''{% extends 'base.html' %}
{% block title %}Docenti{% endblock %}
{% block content %}
<div class="container">
    <h2>Elenco Docenti</h2>
    <a href="{% url 'core:docente_create' %}" class="btn btn-success mb-3">Nuovo Docente</a>
    <table class="table table-striped">
        <thead>
            <tr><th>Nome</th><th>Email</th><th>Cellulare</th><th>Azioni</th></tr>
        </thead>
        <tbody>
            {% for doc in docenti %}
            <tr>
                <td><a href="{% url 'core:docente_detail' doc.pk %}">{{ doc.nome }}</a></td>
                <td>{{ doc.email }}</td>
                <td>{{ doc.cellulare }}</td>
                <td>
                    <a href="{% url 'core:docente_detail' doc.pk %}" class="btn btn-sm btn-info">Dettagli</a>
                    <a href="{% url 'core:docente_update' doc.pk %}" class="btn btn-sm btn-warning">Modifica</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',

    f'{BASE}/anagrafiche/docente_detail.html': '''{% extends 'base.html' %}
{% block title %}{{ docente.nome }}{% endblock %}
{% block content %}
<div class="container">
    <h2>{{ docente.nome }}</h2>
    <div class="card">
        <div class="card-body">
            <p><strong>Email:</strong> {{ docente.email }}</p>
            <p><strong>Telefono:</strong> {{ docente.telefono }}</p>
            <p><strong>Cellulare:</strong> {{ docente.cellulare }}</p>
            <p><strong>Indirizzo:</strong> {{ docente.indirizzo }}</p>
        </div>
    </div>
    <div class="mt-3">
        <a href="{% url 'core:docente_update' docente.pk %}" class="btn btn-warning">Modifica</a>
        <a href="{% url 'core:docente_list' %}" class="btn btn-secondary">Torna all'elenco</a>
    </div>
</div>
{% endblock %}''',

    f'{BASE}/anagrafiche/docente_form.html': '''{% extends 'base.html' %}
{% block title %}Docente{% endblock %}
{% block content %}
<div class="container">
    <h2>{% if object %}Modifica{% else %}Nuovo{% endif %} Docente</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-success">Salva</button>
        <a href="{% url 'core:docente_list' %}" class="btn btn-secondary">Annulla</a>
    </form>
</div>
{% endblock %}''',

    # AUTORITÀ
    f'{BASE}/anagrafiche/autorita_list.html': '''{% extends 'base.html' %}
{% block title %}Autorità{% endblock %}
{% block content %}
<div class="container">
    <h2>Elenco Autorità</h2>
    <a href="{% url 'core:autorita_create' %}" class="btn btn-success mb-3">Nuova Autorità</a>
    <table class="table table-striped">
        <thead>
            <tr><th>Nome</th><th>Carica</th><th>Email</th><th>Azioni</th></tr>
        </thead>
        <tbody>
            {% for aut in autorita %}
            <tr>
                <td><a href="{% url 'core:autorita_detail' aut.pk %}">{{ aut.nome }}</a></td>
                <td>{{ aut.carica }}</td>
                <td>{{ aut.email }}</td>
                <td>
                    <a href="{% url 'core:autorita_detail' aut.pk %}" class="btn btn-sm btn-info">Dettagli</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',

    f'{BASE}/anagrafiche/autorita_detail.html': '''{% extends 'base.html' %}
{% block title %}{{ autorita.nome }}{% endblock %}
{% block content %}
<div class="container">
    <h2>{{ autorita.nome }}</h2>
    <div class="card">
        <div class="card-body">
            <p><strong>Carica:</strong> {{ autorita.carica }}</p>
            <p><strong>Email:</strong> {{ autorita.email }}</p>
            <p><strong>Indirizzo:</strong> {{ autorita.indirizzo }}</p>
        </div>
    </div>
    <div class="mt-3">
        <a href="{% url 'core:autorita_update' autorita.pk %}" class="btn btn-warning">Modifica</a>
        <a href="{% url 'core:autorita_list' %}" class="btn btn-secondary">Torna all'elenco</a>
    </div>
</div>
{% endblock %}''',

    f'{BASE}/anagrafiche/autorita_form.html': '''{% extends 'base.html' %}
{% block title %}Autorità{% endblock %}
{% block content %}
<div class="container">
    <h2>{% if object %}Modifica{% else %}Nuova{% endif %} Autorità</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-success">Salva</button>
        <a href="{% url 'core:autorita_list' %}" class="btn btn-secondary">Annulla</a>
    </form>
</div>
{% endblock %}''',

    # CORSI
    f'{BASE}/corsi/corso_list.html': '''{% extends 'base.html' %}
{% block title %}Corsi{% endblock %}
{% block content %}
<div class="container">
    <h2>Elenco Corsi</h2>
    <a href="{% url 'core:corso_create' %}" class="btn btn-success mb-3">Nuovo Corso</a>
    <table class="table table-striped">
        <thead>
            <tr><th>Codice</th><th>Nome</th><th>Categoria</th><th>Azioni</th></tr>
        </thead>
        <tbody>
            {% for corso in corsi %}
            <tr>
                <td>{{ corso.codice }}</td>
                <td><a href="{% url 'core:corso_detail' corso.pk %}">{{ corso.nome }}</a></td>
                <td>{{ corso.categoria.nome|default:"-" }}</td>
                <td>
                    <a href="{% url 'core:corso_detail' corso.pk %}" class="btn btn-sm btn-info">Dettagli</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',

    f'{BASE}/corsi/corso_detail.html': '''{% extends 'base.html' %}
{% block title %}{{ corso.nome }}{% endblock %}
{% block content %}
<div class="container">
    <h2>{{ corso.nome }}</h2>
    <div class="card">
        <div class="card-body">
            <p><strong>Codice:</strong> {{ corso.codice }}</p>
            <p><strong>Categoria:</strong> {{ corso.categoria.nome|default:"-" }}</p>
            <p><strong>Descrizione:</strong> {{ corso.descrizione }}</p>
        </div>
    </div>
    <div class="mt-3">
        <a href="{% url 'core:corso_update' corso.pk %}" class="btn btn-warning">Modifica</a>
        <a href="{% url 'core:corso_list' %}" class="btn btn-secondary">Torna all'elenco</a>
    </div>
</div>
{% endblock %}''',

    f'{BASE}/corsi/corso_form.html': '''{% extends 'base.html' %}
{% block title %}Corso{% endblock %}
{% block content %}
<div class="container">
    <h2>{% if object %}Modifica{% else %}Nuovo{% endif %} Corso</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-success">Salva</button>
        <a href="{% url 'core:corso_list' %}" class="btn btn-secondary">Annulla</a>
    </form>
</div>
{% endblock %}''',

    # EDIZIONI
    f'{BASE}/corsi/edizione_list.html': '''{% extends 'base.html' %}
{% block title %}Edizioni Corsi{% endblock %}
{% block content %}
<div class="container">
    <h2>Edizioni Corsi - {{ anno_attivo.anno }}</h2>
    <a href="{% url 'core:edizione_create' %}" class="btn btn-success mb-3">Nuova Edizione</a>
    <table class="table table-striped">
        <thead>
            <tr><th>Corso</th><th>Docente</th><th>Q</th><th>Giorni</th><th>Orario</th><th>Iscritti</th><th>Azioni</th></tr>
        </thead>
        <tbody>
            {% for ed in edizioni %}
            <tr>
                <td><a href="{% url 'core:edizione_detail' ed.pk %}">{{ ed.corso.nome }}</a></td>
                <td>{{ ed.docente.nome }}</td>
                <td>{{ ed.quadrimestre.numero }}</td>
                <td>{{ ed.giorni_settimana }}</td>
                <td>{{ ed.ora_inizio }}-{{ ed.ora_fine }}</td>
                <td><span class="badge bg-success">{{ ed.num_iscritti }}</span></td>
                <td>
                    <a href="{% url 'core:edizione_detail' ed.pk %}" class="btn btn-sm btn-info">Dettagli</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',

    f'{BASE}/corsi/edizione_detail.html': '''{% extends 'base.html' %}
{% block title %}{{ edizione.corso.nome }}{% endblock %}
{% block content %}
<div class="container">
    <h2>{{ edizione.corso.nome }}</h2>
    <div class="card">
        <div class="card-body">
            <p><strong>Anno:</strong> {{ edizione.anno_accademico.anno }}</p>
            <p><strong>Docente:</strong> {{ edizione.docente.nome }}</p>
            <p><strong>Quadrimestre:</strong> {{ edizione.quadrimestre }}</p>
            <p><strong>Orario:</strong> {{ edizione.giorni_settimana }} {{ edizione.ora_inizio }}-{{ edizione.ora_fine }}</p>
            <p><strong>Iscritti:</strong> {{ edizione.iscrizioni.count }}</p>
        </div>
    </div>
    <div class="mt-3">
        <a href="{% url 'core:edizione_update' edizione.pk %}" class="btn btn-warning">Modifica</a>
        <a href="{% url 'core:edizione_list' %}" class="btn btn-secondary">Torna</a>
    </div>
</div>
{% endblock %}''',

    f'{BASE}/corsi/edizione_form.html': '''{% extends 'base.html' %}
{% block title %}Edizione Corso{% endblock %}
{% block content %}
<div class="container">
    <h2>{% if object %}Modifica{% else %}Nuova{% endif %} Edizione</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-success">Salva</button>
        <a href="{% url 'core:edizione_list' %}" class="btn btn-secondary">Annulla</a>
    </form>
</div>
{% endblock %}''',
}

# Crea file
for path, content in templates.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'✅ {path}')

print('\n🎉 Template creati!')
