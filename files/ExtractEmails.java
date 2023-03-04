/**
 * Extracts all emails from a file and saves them to another file.
 * If no arguments are passed, the program will ask for the file names.
 * If arguments are passed, the first argument is the input file and the second is the output file.
 *
 * @author: mad4n7 <contact@mad4n7.com>
 * @version: 1.0
 */

import java.util.regex.*;
import java.io.*;

public class ExtractEmails {

    private static final String EMAIL_PATTERN = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,4}";
    public static BufferedReader readFile(String fileName) throws IOException {
        BufferedReader reader = new BufferedReader(new FileReader(fileName));
        return reader;
    }

    public static void saveMatches(BufferedReader reader, PrintWriter writer) {
        try {
            String line = reader.readLine();

            Pattern pattern = Pattern.compile(EMAIL_PATTERN);
            Matcher matcher = pattern.matcher(line);
            while(line != null) {
                matcher = pattern.matcher(line);
                while (matcher.find()) {
                    writer.println(matcher.group());
                }
                line = reader.readLine();
            }

            writer.flush();
        } catch (IOException e) {
            System.out.println("Error: " + e.getMessage());
        }
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String fileName = null;
        String outputFilename = null;

        if (args.length > 0) {
            fileName = args[0];
            outputFilename = args[1];
        } else {
            System.out.println("What file do you want to read?");
            fileName = reader.readLine();
            System.out.println("Where should I write the output?");
            outputFilename = reader.readLine();
        }

        try {
            System.out.printf("Reading file %s%n", fileName);
            System.out.printf("Writing to file %s%n", outputFilename);
            BufferedReader inputFile = readFile(fileName);
            saveMatches(inputFile, new PrintWriter(outputFilename));
        } catch (IOException e) {
            System.out.println("Error: " + e.getMessage());
        }
    }
}