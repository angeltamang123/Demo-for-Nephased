"use client";

import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { LoaderIcon } from "lucide-react";
import Image from "next/image";
import { Skeleton } from "@/components/ui/skeleton";

// Define the shape of a comment
interface CommentType {
  commentId: number;
  text: string;
  sentiment: string | null;
  hidden: boolean;
}

// Define a reusable prop type for the AddCommentForm
interface AddCommentFormProps {
  onAddComment: (text: string) => void;
}

export default function HomePage() {
  const [loading, setLoading] = useState<boolean>(true);

  const [showComments, setShowComments] = useState<boolean>(false);

  const [comments, setComments] = useState<CommentType[]>([
    {
      commentId: 1,
      text: "धेरै समर्थन छ है दाइ। अनि यस्तो मनोरञ्जनात्मक र ज्ञानमूलक भिडियोका लागि धन्यवाद ❤️",
      sentiment: "GENERAL",
      hidden: false,
    },
    {
      commentId: 2,
      text: "सुन तस्करहरूको अपराध भन्दा ठूलो अपराध के छ? यिनलाई कारागारमा सडाएर मार्नु पर्छ!",
      sentiment: "VIOLENCE",
      hidden: true,
    },
  ]);

  const [pendingComments, setPendingComments] = useState<CommentType[]>([]);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // On mount, call /api/init to warm up the model
  useEffect(() => {
    const initModel = async () => {
      try {
        const res = await axios.get("/api/init", { timeout: 120000 });
        if (res.status === 200) setLoading(false);
      } catch (err) {
        console.error("Failed to init model:", err);
        setTimeout(initModel, 10000);
      }
    };
    initModel();
  }, []);

  // Whenever pendingComments changes, reset a 5-second timer
  useEffect(() => {
    if (pendingComments.length > 0) {
      // Clear old timer if exists
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      // Set a new 10-second timer
      timerRef.current = setTimeout(() => {
        batchPredict();
      }, 5000);
    }

    // Cleanup on unmount
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [pendingComments]);

  // Send pending comments to the backend for sentiment
  const batchPredict = async () => {
    if (pendingComments.length === 0) return;

    // Collect just the text
    const texts = pendingComments.map((c) => c.text);
    try {
      const res = await axios.post("/api/predict", { texts });
      if (res.data.status === "ok") {
        const { sentiments } = res.data;

        // Create a copy of existing comments
        const updatedComments = [...comments];
        for (let i = 0; i < sentiments.length; i++) {
          const newComment = { ...pendingComments[i] };
          newComment.sentiment = sentiments[i];

          // If sentiment is VIOLENCE or PROFANITY_1, hide by default
          if (["VIOLENCE", "PROFANITY_1"].includes(sentiments[i])) {
            newComment.hidden = true;
          } else {
            newComment.hidden = false;
          }

          updatedComments.push(newComment);
        }

        // Save updated comments, clear pending
        setComments(updatedComments);
        setPendingComments([]);
      }
    } catch (error) {
      console.error("Error from /api/predict:", error);
    }
  };

  // Add a new comment to the 'pending' queue
  const handleAddComment = (text: string) => {
    const newComment: CommentType = {
      commentId: Math.floor(Math.random() * 100000),
      text,
      sentiment: null,
      hidden: false,
    };
    // Append to pending
    setPendingComments((prev) => [...prev, newComment]);
  };

  // Toggle hidden for an existing comment
  const toggleHidden = (id: number) => {
    setComments((prev) =>
      prev.map((c) => {
        if (c.commentId === id) {
          return { ...c, hidden: !c.hidden };
        }
        return c;
      })
    );
  };

  // Loading state
  if (loading) {
    return (
      <div className="h-screen flex flex-col justify-center items-center">
        <h2 className="text-2xl font-bold animate-pulse">
          Waiting Nephased to
          <span className="animate-fire text-white"> fire-up</span>...
        </h2>
        <br />
        <LoaderIcon className="animate-spin mt-5" />
        <h2 className="text-lg mt-48">This can take a while...</h2>
      </div>
    );
  }

  // Main UI
  return (
    <div className="flex flex-col p-20 justify-center items-center">
      <h1
        className="p-5 mb-4 underline justify-center items-center font-sans text-3xl antialiased font-semibold shadow-orange-500
      transition-all delay-200 shadow-none hover:text-orange-700 hover:shadow-orange-700 
      hover:scale-105 cursor-pointer active:scale-95"
        onClick={() =>
          window.open("https://github.com/angeltamang123/nephased", "_blank")
        }
      >
        Nephased Demo
      </h1>
      <div className="relative h-96 w-full shadow-sm shadow-white bg-white">
        <Image
          src="/penguins.png"
          alt="Penguins"
          fill
          className="object-contain"
        />
      </div>

      <button
        onClick={() => setShowComments(!showComments)}
        className="text-lg mt-2 w-full flex border-2 justify-center border-white border-solid rounded-lg p-2 active:scale-95"
      >
        {showComments ? "Close Comments" : "View Comments"}
      </button>

      {showComments && (
        <div className="flex bg-gray-900 border-2 p-3 pl-10 pr-10 border-white rounded-lg flex-col flex-none mt-5 w-full break-words ">
          {comments.map((c) => (
            <div
              key={c.commentId}
              className=" mb-2 border-b w-full break-words"
            >
              {c.hidden ? (
                <div>
                  <strong className="shadow-transparent">[Censored]</strong>
                  <text>
                    {" "}
                    This Comment has been hidden for {}
                    {c.sentiment === "VIOLENCE" ? "violence" : "profanity"}
                  </text>
                  <button
                    onClick={() => toggleHidden(c.commentId)}
                    className="ml-6 mb-1 border-1 bg-red-700 p-1 rounded-md text-white active:scale-95"
                  >
                    View
                  </button>
                </div>
              ) : (
                <div>
                  {c.text}{" "}
                  {c.sentiment && (
                    <em style={{ color: "white" }}>({c.sentiment})</em>
                  )}
                  {["VIOLENCE", "PROFANITY_1"].includes(c.sentiment ?? "") && (
                    <button
                      className="ml-6 mb-1 border-1 bg-cyan-500 rounded-md p-1 text-white active:scale-95"
                      onClick={() => toggleHidden(c.commentId)}
                    >
                      Hide
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
          {pendingComments.length > 0 &&
            pendingComments.map((c) => (
              <Skeleton className="mt-1 mb-1 h-4 w-[400px]" />
            ))}

          <AddCommentForm onAddComment={handleAddComment} />
        </div>
      )}
    </div>
  );
}

// Separate component for adding comments
function AddCommentForm({ onAddComment }: AddCommentFormProps) {
  const [text, setText] = useState<string>("");

  const handleSubmit = (e?: React.FormEvent<HTMLFormElement>) => {
    if (e) e.preventDefault();
    if (text.trim()) {
      onAddComment(text.trim());
      setText("");
    }
  };

  const handleEnter = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    debugger;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit(e);
        setText("");
      }}
    >
      <div className="flex flex-col mt-2">
        <textarea
          className="text-black w-full p-2 border rounded resize-none"
          placeholder="Add a comment..."
          value={text}
          onKeyDown={handleEnter}
          onChange={(e) => {
            setText(e.target.value);
            e.target.style.height = "40px";
            e.target.style.height = `${e.target.scrollHeight}px`;
          }}
          rows={1}
          style={{ minHeight: "40px", maxHeight: "200px", overflowY: "hidden" }}
        />
        <button
          type="submit"
          className="mt-2 px-4 py-2 border-2 border-orange-700 text-orange-700 font-bold rounded-lg transition-all duration-300 
             hover:bg-orange-700 hover:text-white shadow-lg hover:shadow-orange-700/50 active:scale-95"
        >
          Comment
        </button>
      </div>
    </form>
  );
}
