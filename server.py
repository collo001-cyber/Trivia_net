import socket, threading, time, json, os
from helper.network import send_json, recv_json
from helper.messages import make_question, make_result, make_leaderboard, make_ready, make_finished
from questions import get_questions
import sys

# load config
import json as _json
with open("server_config.json", "r") as f:
    CFG = _json.load(f)

HOST = '0.0.0.0'
PORT = int(os.environ.get("PORT", 10000))  # Use Render's assigned port or default
MIN_PLAYERS = CFG.get("min_players", 2)
JOIN_WAIT = CFG.get("max_wait_seconds_for_players", 30)
Q_PER_GAME = CFG.get("questions_per_game", 5)
Q_SECONDS = CFG.get("seconds_per_question", 15)
INTERVAL = CFG.get("seconds_between_questions", 4)
SCORE_CORRECT = CFG.get("score_for_correct", 1)

lock = threading.Lock()
players = {}   # addr -> {"conn": sock, "username": str, "score": int, "ready": bool}
game_started = threading.Event()

def broadcast(msg):
    with lock:
        for info in list(players.values()):
            try:
                send_json(info["conn"], msg)
            except Exception:
                pass

def handle_client(conn, addr):
    try:
        # initial handshake: expect HI
        data = recv_json(conn, timeout=10)
        if not data or data.get("message_type") != "HI":
            conn.close()
            return

        username = data.get("username", f"Player-{addr[1]}")
        with lock:
            players[addr] = {"conn": conn, "username": username, "score": 0, "ready": True}
            print(f"[+] {username} joined from {addr}. Players: {len(players)}")

        send_json(conn, make_ready("Welcome {}, wait for game to start...".format(username)))

        # If enough players, signal start
        with lock:
            if len(players) >= MIN_PLAYERS:
                game_started.set()

        # keep connection open; all gameplay handled by game loop
        while not game_started.is_set():
            # idle period while waiting for start
            time.sleep(0.5)

        # after game starts, we'll still keep socket open for recv_json calls from game thread
        while True:
            # keep thread alive to detect broken connection
            heartbeat = recv_json(conn, timeout=0.5)
            if heartbeat is None:
                # no data (timeout) is fine. If socket closed, recv_json returns None because chunk empty
                # But we can't be certain of closed socket here; continue
                pass
            time.sleep(0.1)
    except Exception as e:
        # connection error -> mark player but do not remove; scoring rules treat absent players as answered wrong
        print(f"[!] connection error for {addr}: {e}")
    finally:
        # do not remove player, keep them in players map so they appear in leaderboard but their future answers are considered missing
        try:
            conn.close()
        except:
            pass

def accept_loop(server_sock):
    while not game_started.is_set():
        try:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except Exception:
            break

def game_loop():
    print("🔔 Game will begin shortly...")
    # Wait for players up to JOIN_WAIT (or until MIN_PLAYERS reached)
    start_time = time.time()
    while not game_started.is_set() and time.time() - start_time < JOIN_WAIT:
        with lock:
            if len(players) >= MIN_PLAYERS:
                game_started.set()
                break
        time.sleep(0.5)

    with lock:
        if len(players) < 1:
            print("No players connected. Shutting down.")
            return

    print("🎮 Game starting with players:")
    with lock:
        for p in players.values():
            print(" -", p["username"])

    # Broadcast READY for start
    broadcast(make_ready("Game starting now! Get ready."))

    # Select question set
    qset = get_questions(Q_PER_GAME)

    for qid, qtext, choices, correct in qset:
        # send question to everyone
        broadcast(make_question(qid, qtext, choices, Q_SECONDS))
        print(f"📨 Sent Q{qid}: {qtext} | correct={correct}")

        # collect answers over Q_SECONDS
        answers = {}  # addr -> answer string
        q_start = time.time()
        while time.time() - q_start < Q_SECONDS:
            with lock:
                for addr, info in list(players.items()):
                    conn = info["conn"]
                    try:
                        msg = recv_json(conn, timeout=0.2)
                        if msg and msg.get("message_type") == "ANSWER" and msg.get("qid") == qid:
                            answers[addr] = msg.get("answer", "").strip()
                    except Exception:
                        pass
            # if all players answered, break early
            with lock:
                if len(answers) >= len(players):
                    break
            time.sleep(0.05)

        # evaluate answers and send individual results
        with lock:
            for addr, info in list(players.items()):
                given = answers.get(addr, "")
                correct_flag = (given.lower() == correct.lower())
                if correct_flag:
                    info["score"] += SCORE_CORRECT
                # send result
                try:
                    send_json(info["conn"], make_result(correct_flag, given, correct, info["score"]))
                except Exception:
                    pass

        # broadcast leaderboard after question
        with lock:
            lb = sorted(
                [{"username": p["username"], "score": p["score"]} for p in players.values()],
                key=lambda x: x["score"], reverse=True
            )
        broadcast(make_leaderboard(lb))
        time.sleep(INTERVAL)

    # final standings
    with lock:
        final = sorted(
            [{"username": p["username"], "score": p["score"]} for p in players.values()],
            key=lambda x: x["score"], reverse=True
        )
    broadcast(make_leaderboard(final))
    broadcast(make_finished())
    print("🏁 Game finished. Final standings:")
    for i, p in enumerate(final, start=1):
        print(f"{i}. {p['username']} - {p['score']}")

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(32)
    print(f"🟢 Server listening on {HOST}:{PORT}")

    # accept clients in background
    accepter = threading.Thread(target=accept_loop, args=(server_sock,), daemon=True)
    accepter.start()

    # Wait until MIN_PLAYERS or JOIN_WAIT — game_loop will handle this logic
    game_loop()

    # close server after game ends
    try:
        server_sock.close()
    except:
        pass

if __name__ == "__main__":
    import time
import sys

try:
    while True:
        main()
        print("⚠️ No players connected. Waiting before retrying...")
        time.sleep(5)
except KeyboardInterrupt:
    print("Server stopped manually.")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

def run_http_healthcheck():
    port = int(os.environ.get("PORT", 8000))
    handler = SimpleHTTPRequestHandler
    with HTTPServer(("0.0.0.0", port), handler) as httpd:
        print(f"HTTP healthcheck running on port {port}")
        httpd.serve_forever()

# Start the HTTP server in a background thread
threading.Thread(target=run_http_healthcheck, daemon=True).start()
