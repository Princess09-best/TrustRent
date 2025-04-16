const newman = require('newman');
const path = require('path');

const BASE_URL = 'http://localhost:8000';
const COLLECTIONS_DIR = path.join(__dirname);

// Store shared variables between runs
let sharedVariables = {
    base_url: BASE_URL,
    registered_email: '',
    registered_password: '',
    user_id: ''
};

const TEST_COLLECTIONS = [
    'user_registration_tests.json',
    'user_login_tests.json',
    'property_management_tests.json',
    'property_listing_tests.json',
    'property_detail_tests.json'
];

function runCollection(collectionName) {
    return new Promise((resolve, reject) => {
        console.log(`Running collection: ${collectionName}`);
        
        newman.run({
            collection: path.join(COLLECTIONS_DIR, collectionName),
            reporters: ['cli'],
            environment: {
                values: Object.entries(sharedVariables).map(([key, value]) => ({
                    key,
                    value,
                    enabled: true
                }))
            }
        }, function(err, summary) {
            if (err) {
                console.error('Collection run failed:', err);
                reject(err);
                return;
            }

            // Update shared variables from the run
            if (summary.environment) {
                summary.environment.values.members.forEach(({key, value}) => {
                    if (sharedVariables.hasOwnProperty(key)) {
                        console.log(`Updating shared variable ${key} to:`, value);
                        sharedVariables[key] = value;
                    }
                });
            }

            console.log(`Finished running ${collectionName}`);
            resolve(summary);
        });
    });
}

async function runAllCollections() {
    console.log('Starting test suite...');
    console.log('Base URL:', BASE_URL);
    console.log('Collections directory:', COLLECTIONS_DIR);

    for (const collection of TEST_COLLECTIONS) {
        try {
            await runCollection(collection);
        } catch (error) {
            console.error(`Error running collection ${collection}:`, error);
            process.exit(1);
        }
    }

    console.log('All collections completed successfully!');
}

runAllCollections(); 