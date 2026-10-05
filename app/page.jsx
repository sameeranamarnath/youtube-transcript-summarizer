"use client";

import React, { useState } from "react";
import PageHeader from "./components/PageHeader";
import PromptBox from "./components/PromptBox";
import ResultWithSources from "./components/ResultWithSources";
import TwoColumnLayout from "./components/TwoColumnLayout";

const VideoChatUI = () => {
  const [prompt, setPrompt] = useState(
    ""
  );
  const [error, setError] = useState(null);
  const [firstMsg, setFirstMsg] = useState(true);

  // And we'll set an initial message as well, to make the UI look a little nicer.
  const [messages, setMessages] = useState([
    {
      text: `Please provide a YouTube video URL to a relatively short video and I'll answer any questions you have based on the video.
                `,
      type: "bot",
    },
  ]);

  const handlePromptChange = (e) => {
    setPrompt(e.target.value);
  };

  // And the body will send a prompt as well as a firstMsg, which tells us if its the first message in the chat or not
  // Because the first message will tell us to create the YouTube Chat bot
  const handleSubmit = async () => {
    try {
      // Push the user's message into the messages array
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: prompt, type: "user", sourceDocuments: null },
      ]);

      const response = await fetch(`/api/video-chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt, firstMsg }),
      });

      console.log({ response });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const searchRes = await response.json();

      // Push the response into the messages array
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          text: searchRes.output.text,
          type: "bot",
        },
      ]);

      setPrompt("");
      setFirstMsg(false);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Error fetching transcript. Please try again.");
    }
  };

  return (
    <>
      <TwoColumnLayout
        leftChildren={
          <>
            <PageHeader
              heading="GenAI based solution to Q&A on YouTube videos-Amar.S"
              boldText="This bot lets you ask questions based on a given youtube video . "
            />
          </>
        }
        rightChildren={
          <>
            <ResultWithSources messages={messages} pngFile="youtube" />
            <PromptBox
              prompt={prompt}
              handlePromptChange={handlePromptChange}
              handleSubmit={handleSubmit}
              placeHolderText={
                messages.length === 1
                  ? "Enter a youtube url of a short video, e.g., https://www.youtube.com/watch?v=U6BekDyWL08"
                  : "Ask a question based on the video you have provided"
              }
              error={error}
            />
          </>
        }
      />
    </>
  );
};

export default VideoChatUI;
