import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.net.Socket;
import java.util.*;

public class TMPNetworkPanel extends JFrame {

    private static final String BASE =
        new File(".").getAbsolutePath() + "\\";

    private Properties config = new Properties();

    private final Map<String, Process> processes = new HashMap<>();
    private final Map<String, BufferedWriter> inputs = new HashMap<>();
    private final Map<String, JTextArea> consoles = new HashMap<>();
    private final Map<String, JLabel> statusLabels = new HashMap<>();
    private final Map<String, ServerInfo> servers = new LinkedHashMap<>();

    private JTabbedPane tabs = new JTabbedPane();

    public TMPNetworkPanel() {
        loadConfig();
        loadServers();

        setTitle(get("panel.name", "[TMP-Network] Panel"));
        setSize(1000, 700);
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setLayout(new BorderLayout());

        // TOP BAR
        JButton startAllBtn = new JButton("Start ALL");
        JButton stopAllBtn = new JButton("Stop ALL");

        startAllBtn.addActionListener(e -> startAll());
        stopAllBtn.addActionListener(e -> stopAll());

        JPanel topBar = new JPanel();
        topBar.add(startAllBtn);
        topBar.add(stopAllBtn);

        add(topBar, BorderLayout.NORTH);
        add(tabs, BorderLayout.CENTER);

        servers.keySet().forEach(this::createServerTab);

        startMonitoring();
    }

    // ================= CONFIG =================

    private void loadConfig() {
        try (FileInputStream fis = new FileInputStream("config.properties")) {
            config.load(fis);
        } catch (IOException e) {
            System.out.println("[TMP-Network] No config found.");
        }
    }

    private String get(String key, String def) {
        return config.getProperty(key, def);
    }

    private void loadServers() {
        config.forEach((k, v) -> {
            String key = k.toString();
            if (key.startsWith("server.")) {

                String name = key.substring(7);
                String[] parts = v.toString().split(",");

                servers.put(name, new ServerInfo(
                    parts[0],
                    parts[1],
                    Integer.parseInt(parts[2])
                ));
            }
        });
    }

    // ================= UI =================

    private void createServerTab(String name) {

        JTextArea console = new JTextArea();
        console.setEditable(false);

        JScrollPane scroll = new JScrollPane(console);

        JTextField input = new JTextField();
        input.addActionListener(e -> {
            sendCommand(name, input.getText());
            input.setText("");
        });

        JLabel status = new JLabel("Status: OFFLINE");
        statusLabels.put(name, status);

        JButton start = new JButton("Start");
        JButton stop = new JButton("Stop");
        JButton restart = new JButton("Restart");

        start.addActionListener(e -> startServer(name));
        stop.addActionListener(e -> stopServer(name));
        restart.addActionListener(e -> restartServer(name));

        JPanel controls = new JPanel();
        controls.add(start);
        controls.add(stop);
        controls.add(restart);
        controls.add(status);

        JPanel bottom = new JPanel(new BorderLayout());
        bottom.add(input, BorderLayout.CENTER);
        bottom.add(controls, BorderLayout.SOUTH);

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(scroll, BorderLayout.CENTER);
        panel.add(bottom, BorderLayout.SOUTH);

        tabs.add(name, panel);
        consoles.put(name, console);
    }

    // ================= GLOBAL =================

    private void startAll() {
        servers.keySet().forEach(this::startServer);
    }

    private void stopAll() {
        servers.keySet().forEach(this::stopServer);
    }

    // ================= SERVER CONTROL =================

    private void startServer(String name) {
        ServerInfo s = servers.get(name);

        try {
            File dir = s.folder.equals(".")
                ? new File(BASE)
                : new File(BASE + s.folder);

            ProcessBuilder pb = new ProcessBuilder(
                "java",
                "-Xms1G",
                "-Xmx2G",
                "-jar",
                s.jar,
                "nogui"
            );

            pb.directory(dir);
            pb.redirectErrorStream(true);

            Process p = pb.start();
            processes.put(name, p);

            BufferedWriter writer =
                new BufferedWriter(new OutputStreamWriter(p.getOutputStream()));
            inputs.put(name, writer);

            consoles.get(name).append("[TMP] STARTING...\n");
            setStatus(name, "STARTING");

            new Thread(() -> readOutput(name, p)).start();

        } catch (IOException e) {
            consoles.get(name).append("[TMP] FAILED TO START\n");
        }
    }

    private void restartServer(String name) {
        stopServer(name);
        new Thread(() -> {
            try { Thread.sleep(3000); } catch (Exception ignored) {}
            startServer(name);
        }).start();
    }

    private void stopServer(String name) {
        sendCommand(name, "stop");
    }

    // ================= OUTPUT =================

    private void readOutput(String name, Process p) {
        try (BufferedReader r =
                 new BufferedReader(new InputStreamReader(p.getInputStream()))) {

            String line;
            while ((line = r.readLine()) != null) {

                String l = line;
                SwingUtilities.invokeLater(() ->
                    consoles.get(name).append(l + "\n")
                );

                if (line.contains("Done")) {
                    setStatus(name, "ONLINE");
                }
            }

        } catch (IOException ignored) {}

        setStatus(name, "OFFLINE");
    }

    // ================= COMMAND =================

    private void sendCommand(String name, String cmd) {
        try {
            BufferedWriter w = inputs.get(name);
            if (w != null) {
                w.write(cmd);
                w.newLine();
                w.flush();

                consoles.get(name).append("[CMD] " + cmd + "\n");
            }
        } catch (IOException ignored) {}
    }

    // ================= MONITOR =================

    private void startMonitoring() {
        new Thread(() -> {
            while (true) {
                try {
                    Thread.sleep(5000);

                    servers.forEach((name, s) -> {
                        setStatus(name,
                            isOnline(s.port) ? "ONLINE" : "OFFLINE"
                        );
                    });

                } catch (InterruptedException ignored) {}
            }
        }).start();
    }

    private boolean isOnline(int port) {
        try (Socket s = new Socket("localhost", port)) {
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    // ================= STATUS =================

    private void setStatus(String name, String status) {
        SwingUtilities.invokeLater(() ->
            statusLabels.get(name).setText("Status: " + status)
        );
    }

    // ================= MODEL =================

    static class ServerInfo {
        String folder, jar;
        int port;

        ServerInfo(String f, String j, int p) {
            folder = f;
            jar = j;
            port = p;
        }
    }

    public static void main(String[] args) {
        new TMPNetworkPanel().setVisible(true);
    }
}