(function() {
    'use strict';

    let validationTimeout;
    const usernameInput = document.getElementById('username');
    const submitButton = document.getElementById('submit-button');
    const validationMessage = document.getElementById('validation-message');
    const validationWrapper = document.getElementById('validation-wrapper');
    const teamDetails = document.getElementById('team-details');
    const createPublisherForm = document.getElementById('create-publisher-form');

    if (!createPublisherForm) {
        return;
    }

    const validationUrl = createPublisherForm.dataset.validationUrl;

    usernameInput.addEventListener('input', function() {
        clearTimeout(validationTimeout);
        const username = this.value.trim();

        if (!username) {
            validationMessage.textContent = '';
            validationWrapper.classList.remove('is-error', 'is-success');
            submitButton.disabled = true;
            teamDetails.classList.add('u-hide');
            return;
        }

        validationMessage.innerHTML = '<i class="p-icon--spinner u-animation--spin"></i> Checking Launchpad...';
        validationWrapper.classList.remove('is-error', 'is-success');
        submitButton.disabled = true;
        teamDetails.classList.add('u-hide');

        validationTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`${validationUrl}?username=${encodeURIComponent(username)}`);
                const data = await response.json();

                if (response.ok && data.exists && !data.already_created) {
                    validationMessage.textContent = 'Team found on Launchpad';
                    validationWrapper.classList.remove('is-error');
                    validationWrapper.classList.add('is-success');

                    document.getElementById('team-name').textContent = data.name;
                    document.getElementById('team-display-name').textContent = data.display_name;
                    document.getElementById('team-link').textContent = data.web_link;
                    document.getElementById('team-link').href = data.web_link;
                    document.getElementById('publisher-id').textContent = data.publisher_id;
                    teamDetails.classList.remove('u-hide');

                    submitButton.disabled = false;
                } else if (response.status >= 400 && response.status < 500) {
                    validationMessage.textContent = data.message || 'Error validating team';
                    validationWrapper.classList.remove('is-success');
                    validationWrapper.classList.add('is-error');
                    submitButton.disabled = true;
                    teamDetails.classList.add('u-hide');
                } else {
                    validationMessage.textContent = 'Error validating team';
                    validationWrapper.classList.remove('is-success');
                    validationWrapper.classList.add('is-error');
                    submitButton.disabled = true;
                    teamDetails.classList.add('u-hide');
                }
            } catch (error) {
                validationMessage.textContent = 'Connection error';
                validationWrapper.classList.remove('is-success');
                validationWrapper.classList.add('is-error');
                submitButton.disabled = true;
                teamDetails.classList.add('u-hide');
            }
        }, 500);
    });

    createPublisherForm.addEventListener('submit', function() {
        submitButton.disabled = true;
        submitButton.classList.add('is-loading');
        submitButton.innerHTML = '<i class="p-icon--spinner u-animation--spin is-dark"></i> Creating...';
    });
})();
