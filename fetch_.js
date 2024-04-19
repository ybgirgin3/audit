var categoryId = 1;
// var topicSelect = document.getElementById('topicSelect');

// Clear previous options
// topicSelect.innerHTML = '<option value="">Select Topic</option>';
// topicSelect.disabled = true;

if (categoryId) {
    // Fetch topics based on selected category
    fetch('http://127.0.0.1:8000/management/get_topics/' + categoryId)
        .then(response => response.json())
        .then(data => {
            data.forEach(topic => {
                console.log(topic.name, topic.id)
                // var option = document.createElement('option');
                // option.text = topic.name;
                // option.value = topic.id;
                // topicSelect.appendChild(option);
            });
            // topicSelect.disabled = false;
        })
        .catch(error => console.error('Error:', error));
}
