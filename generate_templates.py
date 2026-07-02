"""
Script per generare template mancanti
"""

import os

BASE_DIR = 'core/templates'

# Template da generare
templates = {
    'anagrafiche/docente_list.html': '''{% extends 'base.html' %}
{% block title %}Elenco Docenti{% endblock %}
{% block content %}
<div class="container">
    <h2><i class="bi bi-person-badge text-primary"></i> Elenco Docenti</h2>
    <a href="{% url 'core:docente_create' %}" class="btn btn-success mb-3">Nuovo Docente</a>
    <table class="table table-striped">
        <thead>
            <tr><th>Nome</th><th>Email</th><th>Telefono</th><th>Azioni</th></tr>
        </thead>
        <tbody>
            {% for docente in docenti %}
            <tr>
                <td><a href="{% url 'core:docente_detail' docente.pk %}">{{ docente.nome }}</a></td>
                <td>{{ docente.email }}</td>
                <td>{{ docente.cellulare }}</td>
                <td>
                    <a href="{% url 'core:docente_detail' docente.pk %}" class="btn btn-sm btn-info">Dettagli</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',

    'anagrafiche/docente_detail.html': '''{% extends 'base.html' %}
{% block title %}{{ docente.nome }}{% endblock %}
{% block content %}
<div class="container">
    <h2>{{ docente.nome }}</h2>
    <p><strong>Email:</strong> {{ docente.email }}</p>
    <p><strong>Telefono:</strong> {{ docente.telefono }}</p>
    <p><strong>Cellulare:</strong> {{ docente.cellulare }}</p>
    <a href="{% url 'core:docente_update' docente.pk %}" class="btn btn-warning">Modifica</a>
    <a href="{% url 'core:docente_list' %}" class="btn btn-secondary">Torna all'elenco</a>
</div>
{% endblock %}''',

    'anagrafiche/docente_form.html': '''{% extends 'base.html' %}
{% block title %}Modifica Docente{% endblock %}
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
}

# Genera file
for path, content in templates.items():
    filepath = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'✅ Creato: {filepath}')

print('\n🎉 Template generati!')
