# Firebase Integration Guide

This guide provides a quick start for deploying the application to Firebase, along with detailed steps for setting up the Firebase project and configuring the deployment.

## Quick Start

1.  **Install Firebase CLI:**
    ```bash
    npm install -g firebase-tools
    ```

2.  **Login to Firebase:**
    ```bash
    firebase login
    ```

3.  **Initialize Firebase:**
    ```bash
    firebase init
    ```
    - Select "Hosting" and "Functions".
    - Choose an existing project or create a new one.
    - Use the `frontend/out` directory as the public directory.
    - Configure as a single-page app (rewrite all urls to /index.html).
    - Do not overwrite existing files.

4.  **Deploy to Firebase:**
    ```bash
    firebase deploy
    ```

## Detailed Steps

### 1. Create a Firebase Project

1.  Go to the [Firebase console](https://console.firebase.google.com/).
2.  Click "Add project" and follow the on-screen instructions.
3.  Once the project is created, you will be redirected to the project dashboard.

### 2. Configure Firebase Hosting

1.  In the Firebase console, go to the "Hosting" section.
2.  Click "Get started" and follow the on-screen instructions.
3.  You will be prompted to install the Firebase CLI and initialize your project.

### 3. Configure Firebase Functions

1.  In the Firebase console, go to the "Functions" section.
2.  Click "Get started" and follow the on-screen instructions.
3.  You will be prompted to install the Firebase CLI and initialize your project.

### 4. Configure the Backend

1.  In the `backend` directory, create a `.env` file with the following content:
    ```
    DATABASE_URL=your-database-url
    SECRET_KEY=your-secret-key
    ```
2.  In the `backend` directory, install the dependencies:
    ```bash
    poetry install
    ```

### 5. Configure the Frontend

1.  In the `frontend` directory, create a `.env.local` file with the following content:
    ```
    NEXT_PUBLIC_API_URL=your-api-url
    ```
2.  In the `frontend` directory, install the dependencies:
    ```bash
    npm install
    ```
3.  Build the frontend:
    ```bash
    npm run build
    ```

### 6. Deploy to Firebase

1.  Deploy the application to Firebase:
    ```bash
    firebase deploy
    ```
2.  After the deployment is complete, you will be able to access the application at the URL provided by Firebase.
