import socket, threading, time
from helper.network import send_json, recv_json

SERVER = "127.0.0.1"
PORT = 7777

def input_with_timeout(prompt, timeout):
    """Ask input if available within timeout; else return empty string."""
    print(prompt, end="", flush=True)
    result = []
    def reader():
        try:
            s = input()
            result.append(s)
        except EOFError:
            pass

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    t.join(timeout)
    if result:
        return result[0]
    return ""

def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER, PORT))
    print(f"✅ Connected to server {SERVER}:{PORT}")

    username = input("Enter your username: ").strip() or f"Player{int(time.time())%1000}"
    send_json(sock, {"message_type":"HI", "username": username})

    try:
        while True:
            msg = recv_json(sock, timeout=None)
            if msg is None:
                print("🔌 Connection closed by server.")
                break

            m = msg.get("message_type")

            if m == "READY":
                print("\n[SERVER] " + msg.get("text", ""))

            elif m == "QUESTION":
                qid = msg.get("qid")
                qtext = msg.get("question")
                choices = msg.get("choices", [])
                time_allowed = msg.get("time_allowed", 15)
                print(f"\n❓ Q{qid}: {qtext}")
                for i, c in enumerate(choices, start=1):
                    print(f"  {i}. {c}")

                # prompt with timeout
                ans = input_with_timeout(f"Your answer (1-{len(choices)}) — you have {time_allowed}s: ", time_allowed)
                answer_text = ""
                if ans:
                    try:
                        idx = int(ans.strip())
                        if 1 <= idx <= len(choices):
                            answer_text = choices[idx-1]
                        else:
                            answer_text = ans.strip()
                    except ValueError:
                        answer_text = ans.strip()
                else:
                    print("\n⏱ Time is up (no answer). Sending empty answer.")

                send_json(sock, {"message_type":"ANSWER", "qid": qid, "answer": answer_text})

            elif m == "RESULT":
                correct = msg.get("correct", False)
                ans = msg.get("answer","")
                corr = msg.get("correct_answer","")
                score = msg.get("score",0)
                if correct:
                    print(f"✅ Correct! You answered: {ans}. Score: {score}")
                else:
                    print(f"❌ Wrong. You answered: '{ans}'. Correct: '{corr}'. Score: {score}")

            elif m == "LEADERBOARD":
                print("\n🏆 Leaderboard:")
                for i, p in enumerate(msg.get("players", []), start=1):
                    print(f"  {i}. {p['username']} — {p['score']} pts")

            elif m == "FINISHED":
                print("\n🎉 " + msg.get("text","Game finished."))
                break

            else:
                print("Unknown message:", msg)

    except KeyboardInterrupt:
        print("\nExiting client.")
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    start_client()
