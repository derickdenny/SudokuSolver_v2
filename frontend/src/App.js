import React, { useState } from 'react';

// Main App component for the Sudoku Image Solver UI
const App = () => {
    // State to hold the solved Sudoku board received from the backend.
    // Initialized as an empty 9x9 grid.
    const [board, setBoard] = useState(
        Array(9).fill(Array(9).fill(''))
    );

    // State to store the image file selected by the user.
    const [selectedImage, setSelectedImage] = useState(null);

    // State to store the base64 encoded image with the solution overlaid, received from the backend.
    const [solvedImage, setSolvedImage] = useState(null);

    // Loading state: true when an API request is in progress.
    const [loading, setLoading] = useState(false);

    // State to store any error messages from the API or client-side validation.
    const [errorMessage, setErrorMessage] = useState('');

    // --- Configuration ---
    // Base URL for your Flask backend.
    // IMPORTANT: Ensure this matches the host and port your Flask app is running on.
    const API_BASE_URL = 'http://localhost:5000'; // Default Flask port

    /**
     * Handles changes in individual Sudoku cells.
     * This function is primarily for manual input into the grid, if the user wanted to.
     * When solving via image, the board is updated directly from the backend response.
     * @param {number} row - The row index of the cell (0-8).
     * @param {number} col - The column index of the cell (0-8).
     * @param {string} value - The new value of the cell (expected to be '1'-'9' or '').
     */
    const handleCellChange = (row, col, value) => {
        // Sanitize input: allow only single digits from 1-9 or empty string.
        const sanitizedValue = value.replace(/[^1-9]/g, '').slice(0, 1);

        // Create a new board array to ensure immutability (important for React state updates).
        const newBoard = board.map((r, rIdx) =>
            r.map((c, cIdx) => {
                if (rIdx === row && cIdx === col) {
                    return sanitizedValue; // Update the specific cell
                }
                return c; // Keep other cells as they are
            })
        );
        setBoard(newBoard); // Update the React state with the new board.
        setErrorMessage(''); // Clear any previous error messages when user interacts.
    };

    /**
     * Handles the selection of an image file from the input field.
     * @param {object} event - The DOM event object from the file input.
     */
    const handleImageChange = (event) => {
        const file = event.target.files[0]; // Get the first selected file.
        if (file) {
            setSelectedImage(file);        // Store the file in state.
            setSolvedImage(null);          // Clear any previously displayed solved image.
            setBoard(Array(9).fill(Array(9).fill(''))); // Clear the grid on new image selection.
            setErrorMessage('');           // Clear any error messages.
        }
    };

    /**
     * Sends the selected Sudoku image to the Python Flask backend for solving.
     * This is an asynchronous function because it involves a network request.
     */
    const solveSudokuFromImage = async () => {
        // Client-side validation: check if an image is selected.
        if (!selectedImage) {
            setErrorMessage('Please select an image first before trying to solve.');
            return;
        }

        setLoading(true);    // Set loading state to true to show a spinner/disable buttons.
        setErrorMessage(''); // Clear previous error messages.
        setSolvedImage(null); // Clear any old solved image display.

        // Create FormData to send the image file to the backend.
        // FormData is used for sending data that typically comes from HTML forms,
        // especially when dealing with file uploads.
        const formData = new FormData();
        formData.append('image', selectedImage); // 'image' should match the key expected by Flask (request.files['image']).

        try {
            // Make a POST request to your Flask backend's /solve_sudoku endpoint.
            const response = await fetch(`${API_BASE_URL}/solve_sudoku`, {
                method: 'POST', // Use POST method for sending data
                body: formData, // The FormData object contains the image file
            });

            // Check if the HTTP response was successful (status code 200-299).
            if (!response.ok) {
                // If the response is not OK, parse the error message from the backend.
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            // Parse the JSON response from the backend.
            const data = await response.json();

            // Update the React board state with the solved numbers.
            setBoard(data.solved_board);
            // Update the state with the base64 encoded solved image for display.
            setSolvedImage(data.solved_image);

            // Provide user feedback. (Consider a custom modal instead of alert for better UX).
            alert('Sudoku solved successfully! Check the grid and solved image.');

        } catch (error) {
            // Catch and display any errors that occur during the fetch operation.
            console.error('Error solving Sudoku:', error);
            setErrorMessage(`Failed to solve Sudoku: ${error.message}. Please try again or with a different image.`);
        } finally {
            setLoading(false); // Reset loading state regardless of success or failure.
        }
    };

    /**
     * Clears the Sudoku board, selected image, and solved image display.
     */
    const clearBoard = () => {
        setBoard(Array(9).fill(Array(9).fill(''))); // Reset board to empty.
        setSelectedImage(null);                     // Clear selected image file.
        setSolvedImage(null);                       // Clear solved image display.
        setErrorMessage('');                        // Clear error messages.

        // Reset the file input element's value to allow selecting the same file again if needed.
        const fileInput = document.getElementById('imageUpload');
        if (fileInput) fileInput.value = '';

        alert('Board and images cleared!'); // User feedback.
    };

    return (
        // Main container for the entire application.
        <div className="min-h-screen bg-gradient-to-br from-blue-100 to-indigo-200 flex flex-col items-center justify-center p-4 font-sans antialiased">
            {/* Tailwind CSS CDN for styling. */}
            <script src="https://cdn.tailwindcss.com"></script>
            {/* Google Fonts for 'Inter' font. */}
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />

            {/* Central content container with shadow and rounded corners. */}
            <div className="bg-white p-6 rounded-xl shadow-2xl max-w-3xl w-full transform transition-all duration-300">
                <h1 className="text-4xl font-bold text-center text-gray-800 mb-6">Sudoku Image Solver</h1>

                {/* Image Upload Section */}
                <div className="mb-6 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center bg-gray-50 hover:border-blue-400 transition-colors duration-200">
                    <label htmlFor="imageUpload" className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium">
                        <input
                            id="imageUpload"
                            type="file"
                            accept="image/*" // Only accept image files
                            onChange={handleImageChange}
                            className="hidden" // Hide the default file input button
                        />
                        {/* Display selected file name or a prompt to upload */}
                        {selectedImage ? (
                            `Selected: ${selectedImage.name}`
                        ) : (
                            <span className="flex items-center justify-center space-x-2">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 0115.9 6L16 6a3 3 0 013 3v10a2 2 0 01-2 2H7a2 2 0 01-2-2v-5l-1-1m0 0l-3 3m3-3l3 3" />
                                </svg>
                                <span>Click to upload Sudoku image</span>
                            </span>
                        )}
                    </label>
                    {selectedImage && (
                        <p className="text-sm text-gray-500 mt-2">
                            {selectedImage.name} ({Math.round(selectedImage.size / 1024)} KB)
                        </p>
                    )}
                </div>

                {/* Error Message Display */}
                {errorMessage && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                        <strong className="font-bold">Error! </strong>
                        <span className="block sm:inline">{errorMessage}</span>
                    </div>
                )}

                {/* Grid and Solved Image Display Area */}
                <div className="flex flex-col md:flex-row gap-8 items-start justify-center">
                    {/* Sudoku Grid Display */}
                    <div className="grid grid-cols-9 border-4 border-gray-800 rounded-lg overflow-hidden flex-shrink-0 w-full md:w-[450px] md:h-[450px]">
                        {board.map((row, rowIndex) => (
                            row.map((cell, colIndex) => (
                                <input
                                    key={`${rowIndex}-${colIndex}`}
                                    type="text"
                                    maxLength="1"
                                    // Display 0 as empty string, otherwise display the cell value.
                                    value={cell === 0 ? '' : cell}
                                    onChange={(e) => handleCellChange(rowIndex, colIndex, e.target.value)}
                                    className={`
                                        w-full h-12 text-center text-2xl font-semibold
                                        border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400
                                        ${(rowIndex === 2 || rowIndex === 5) ? 'border-b-4 border-b-gray-800' : ''}
                                        ${(colIndex === 2 || colIndex === 5) ? 'border-r-4 border-r-gray-800' : ''}
                                        ${cell !== '' && cell !== 0 ? 'bg-indigo-50 text-gray-900' : 'bg-white text-gray-700'}
                                        hover:bg-blue-50 transition-colors duration-150
                                    `}
                                    style={{
                                        // Apply rounded corners only to the outermost cells of the entire grid
                                        borderTopLeftRadius: rowIndex === 0 && colIndex === 0 ? '0.5rem' : '0',
                                        borderTopRightRadius: rowIndex === 0 && colIndex === 8 ? '0.5rem' : '0',
                                        borderBottomLeftRadius: rowIndex === 8 && colIndex === 0 ? '0.5rem' : '0',
                                        borderBottomRightRadius: rowIndex === 8 && colIndex === 8 ? '0.5rem' : '0',
                                    }}
                                />
                            ))
                        ))}
                    </div>

                    {/* Solved Image Display */}
                    {solvedImage && (
                        <div className="flex-grow w-full md:w-[450px] md:h-[450px] flex flex-col items-center">
                            <h3 className="text-xl font-bold text-gray-700 mb-2">Solved Image</h3>
                            {/* Display the base64 encoded image received from the backend */}
                            <img
                                src={`data:image/png;base64,${solvedImage}`}
                                alt="Solved Sudoku"
                                className="rounded-lg shadow-md w-full h-full object-contain border-4 border-gray-800"
                            />
                        </div>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4 mt-8">
                    <button
                        onClick={solveSudokuFromImage}
                        disabled={loading || !selectedImage} // Disable if loading or no image is selected
                        className={`
                            px-8 py-3 rounded-full text-white font-semibold text-lg
                            bg-blue-600 hover:bg-blue-700 active:bg-blue-800
                            shadow-lg transform transition-all duration-200
                            ${loading || !selectedImage ? 'opacity-70 cursor-not-allowed animate-pulse' : 'hover:scale-105'}
                        `}
                    >
                        {loading ? 'Solving...' : 'Solve from Image'}
                    </button>
                    <button
                        onClick={clearBoard}
                        disabled={loading} // Disable while solving is in progress
                        className={`
                            px-8 py-3 rounded-full text-blue-700 font-semibold text-lg
                            bg-white border-2 border-blue-600 hover:bg-blue-50
                            shadow-lg transform transition-all duration-200
                            ${loading ? 'opacity-70 cursor-not-allowed' : 'hover:scale-105'}
                        `}
                    >
                        Clear Board
                    </button>
                </div>

                {/* Instructions and Important Notes */}
                <p className="text-center text-gray-600 text-sm mt-8">
                    Upload an image of a Sudoku puzzle. The system will detect the numbers, solve the puzzle, and display the solution on the grid and overlaid on the image.
                </p>
                <p className="text-center text-sm mt-2 text-red-600 font-semibold">
                    ❗ Important: This web application requires a Python backend to be running locally to process the image and solve the puzzle.
                </p>
                <p className="text-center text-sm mt-1 text-gray-500">
                    Ensure your Flask backend (`app.py`) is running on `http://localhost:5000`.
                </p>
            </div>
        </div>
    );
};

export default App;
