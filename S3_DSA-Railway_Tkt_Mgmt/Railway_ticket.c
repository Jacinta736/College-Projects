#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define ROWS 20
#define COLS 4 
#define TOTAL_SEATS (ROWS * COLS)

struct Passenger {
    int ticket_id;                          
    char name[70];
    int age;
    char seat_no[5];                                                 //Seat number like "2A" '19D'
    struct Passenger *next;
};

struct Passenger *head = NULL;
struct Passenger *waiting_head = NULL;     

int seats[ROWS][COLS] = {0};                                         // 0 = available, 1 = booked                                   ----------------------
int ticket_counter = 1;                    

struct Passenger * createPassenger(char name[], int age, const char seat_choice[]) {
    struct Passenger * newNode = malloc(sizeof(struct Passenger));
    newNode->ticket_id = ticket_counter++;
    strcpy(newNode->name, name);
    newNode->age = age;
    strcpy(newNode->seat_no , seat_choice);
    newNode->next = NULL;
    return newNode;
}

void addPassenger(struct Passenger **head_ref, struct Passenger *newPassenger) {
    if (*head_ref == NULL) {
        *head_ref = newPassenger;
    } else {
        struct Passenger *temp = *head_ref;
        while (temp->next != NULL)
            temp = temp->next;
        temp->next = newPassenger;
    }
}

void displaySeats() {                                                                          
    printf("\t A\tB\tC\tD\n");
    for (int i=0; i<ROWS; i++){
        printf("%d\t",i+1);
        for (int j=0; j<COLS; j++){
            printf("%d\t",seats[i][j]);
        }
        printf("\n");
    }
}

void bookTicket() {
    char name[70];
    int age, num_seats;
    char seat_choice[5];   

    printf("Enter number of seats to book: ");
    scanf("%d", &num_seats);

    if (num_seats < 1 || num_seats > (ROWS * COLS)) {
        printf("Invalid number of seats!\n");
        return;
    }

    for (int i = 0; i < num_seats; i++) {
        printf("\nEnter Name: ");
        scanf("%s", name);
        printf("Enter Age: ");
        scanf("%d", &age);
        printf("Enter Seat Number (e.g., 2B): ", i + 1);
        scanf("%s", seat_choice);

        int row;
        char colChar;
        if (sscanf(seat_choice, "%d%c", &row, &colChar) == 2) {
            row--;                                                   // convert to 0-based
            colChar = toupper(colChar);                              // normalize seat letter
            int col = colChar - 'A';

            if (row >= 0 && row < ROWS && col >= 0 && col < COLS) {
                if (seats[row][col] == 0) {
                    seats[row][col] = 1;
                    sprintf(seat_choice, "%d%c", row+1, colChar);    // store uppercase
                    struct Passenger *newPassenger = createPassenger(name, age, seat_choice);
                    addPassenger(&head, newPassenger);

                    printf("\n--- Ticket Booked Successfully ---\n");
                    printf("Ticket ID : %d\n", newPassenger->ticket_id);
                    printf("Name      : %s\n", newPassenger->name);
                    printf("Age       : %d\n", newPassenger->age);
                    printf("Seat No   : %s\n", newPassenger->seat_no);
                } else {
                    printf("\nSeat %s already booked! Adding to waiting list...\n", seat_choice);
                    struct Passenger *newPassenger = createPassenger(name, age, "WL"); // WL = Waiting List
                    addPassenger(&waiting_head, newPassenger);
                    printf("Added to waiting list.\n");
                    printf("Waiting Ticket ID : %d\n", newPassenger->ticket_id);
                    printf("Name              : %s\n", newPassenger->name);
                    printf("Age               : %d\n", newPassenger->age);
                }
            } else {
                printf("Invalid seat label!\n");
            }
        } else {
            printf("Invalid seat format!\n");
        }
    }
}


void cancelTicket() {
    int ticket_id;
    printf("\nEnter Ticket ID to cancel: ");
    scanf("%d", &ticket_id);

    struct Passenger *temp = head, *prev = NULL;

    while (temp != NULL && temp->ticket_id != ticket_id) {
        prev = temp;
        temp = temp->next;
    }

    if (temp == NULL) {
        printf("Ticket not found!\n");
        return;
    }

    if (strcmp(temp->seat_no, "WL") != 0) {
        int row; char colChar;
        if (sscanf(temp->seat_no, "%d%c", &row, &colChar) == 2) {
            row--;                       
            colChar = toupper(colChar) - 'A';
            int col = colChar - 'A';
            if (row >= 0 && row < ROWS && col >= 0 && col < COLS) {
                seats[row][col] = 0;                                 // free the seat
            }
        }
    }

    if (prev == NULL)
        head = temp->next;
    else
        prev->next = temp->next;

    printf("Ticket ID %d cancelled successfully!\n", ticket_id);
    free(temp);

    if (waiting_head != NULL) {
        struct Passenger *wait = waiting_head;
        waiting_head = waiting_head->next;
        int assigned = 0;
        for (int i=0; i<ROWS && !assigned; i++) {
            for (int j=0; j<COLS && !assigned; j++) {
                if (seats[i][j] == 0) {
                    seats[i][j] = 1;
                    sprintf(wait->seat_no, "%d%c", i+1, 'A'+j);
                    assigned = 1;
                }
            }
        }

        if (assigned) {
            addPassenger(&head, wait);
            printf("\n--- Waiting Passenger Allocated Seat ---\n");
            printf("Ticket ID : %d\n", wait->ticket_id);
            printf("Name      : %s\n", wait->name);
            printf("Age       : %d\n", wait->age);
            printf("Seat No   : %s\n", wait->seat_no);
        }
    }
}

void displayPassengers() {
    struct Passenger *temp = head;
    if (temp == NULL) {
        printf("\nNo confirmed bookings yet!\n");
        return;
    }
    printf("\n--- Confirmed Passenger List ---\n");
    while (temp != NULL) {
        printf("Ticket ID: %d | Name: %s | Age: %d | Seat No: %s\n",
               temp->ticket_id, temp->name, temp->age, temp->seat_no);
        temp = temp->next;
    }
}

int main() {
    int choice;
    while (1) {
        printf("\n=== Railway/Bus Ticket Booking System ===\n");
        printf("1. Show Seat Availability\n");
        printf("2. Book Ticket\n");
        printf("3. Cancel Ticket\n");
        printf("4. View Passenger List\n");
        printf("5. Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1: displaySeats(); break;
            case 2: bookTicket(); break;
            case 3: cancelTicket(); break;
            case 4: displayPassengers(); break;
            case 5: printf("Exiting... Thank you!\n"); exit(0);
            default: printf("Invalid choice!\n");
        }
    }
    return 0;
}