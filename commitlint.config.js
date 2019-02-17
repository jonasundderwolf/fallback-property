module.exports = {
    extends: ['@commitlint/config-angular'],
    rules: {
        'subject-case': [
            2,
            'never',
            ['start-case', 'pascal-case', 'upper-case']
        ],
    }
};
