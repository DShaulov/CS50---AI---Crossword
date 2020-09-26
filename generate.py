import sys
import copy

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # for every value in the domain, if value is longer than constraint, remove it
        for variable in self.domains:
            values_to_be_removed = []
            for value in self.domains[variable]:
                if len(value) > variable.length:
                    values_to_be_removed.append(value)

            for value in values_to_be_removed:
                self.domains[variable].remove(value)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # for every possible word in x, there must be a word in y that starts with the same char at the overlap
        revision_made = False
        overlap_index = self.crossword.overlaps[(x, y)]
        x_values_to_be_removed = []
        for val_x in self.domains[x]:
            found_y = False
            for val_y in self.domains[y]:
                try:
                    if val_x[overlap_index[0]] == val_y[overlap_index[1]]:
                        found_y = True
                        break
                except IndexError:
                    continue

            if found_y == False:
                x_values_to_be_removed.append(val_x)
                revision_made = True

        for value in x_values_to_be_removed:
            self.domains[x].remove(value)
    
        return revision_made

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # if arcs == None, start with an initial queue of all the arcs in the problem
        if arcs == None:
            arc_queue = []
            for arc in self.crossword.overlaps:
                arc_queue.append(arc)

        while len(arc_queue) != 0:
            arc = arc_queue.pop(0)
            # if there is no overlap between the variables, continue
            if self.crossword.overlaps[arc] == None:
                continue
            else:
                revision_made =  self.revise(arc[0], arc[1])
                
            # if during revision, all values from a domain have been removed, return false
            if len(self.domains[arc[0]]) == 0:
                return False 
            # if a revision has been made to x, add to the queue all arcs that have x as the "destination"            
            if revision_made == True:
                for potential_arc in self.crossword.overlaps:
                    if arc[0] == potential_arc[1]:
                        arc_queue.append(potential_arc)

        return True
         

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        assignment_complete = True
        for var in assignment:
            if assignment[var] == None:
                assignment_complete = False
        
        return assignment_complete

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # An assignment is consistent if it satisfies all of the constraints of the problem:
        # that is to say, all values are distinct, every value is the correct length,
        # and there are no conflicts between neighboring variables.

        
        for var in assignment:
            # if no value (word) has been assigned, continue
            if assignment[var] == None:
                continue
            # check to see if every word is unique
            for comp_var in assignment:
                if var == comp_var:
                    continue
                if assignment[var] == assignment[comp_var] and assignment[var] != None:
                    return False

            # check to see if every value is in the correct length
            if len(assignment[var]) != var.length:
                return False
        
            # check to see if there are no conflicting characters between neighboring variables
            var_neighbors = self.crossword.neighbors(var)
            for neighbor_var in var_neighbors:
                # if the neighboring var doesnt have a value assigned, continue
                if assignment[neighbor_var] == None:
                    continue
                # get the overlap between var and his neighbor
                overlap_index = self.crossword.overlaps[(var, neighbor_var)]
                if overlap_index == None:
                    continue
                # compare characters at overlap indices
                if assignment[var][overlap_index[0]] != assignment[neighbor_var][overlap_index[1]]:
                    return False

        return True

        
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        all_var_values = self.domains[var]

        # create a dictionary for mapping values to eliminations
        value_elimination_dict = {}
        for value in all_var_values:
            value_elimination_dict[value] = None
        
        # get a list of all of var's neighbors
        var_neighbors = self.crossword.neighbors(var)
        # for every value in domains[var], count how many variables are ruled out for neighboring variables
        for value in self.domains[var]:
            num_ruled_out = 0
            for neighbor_var in var_neighbors:
                # if neighbor_var has already been assigned in assignment, dont count it
                if assignment[neighbor_var] != None:
                    continue
                for comp_value in self.domains[neighbor_var]:
                    # check how many values are ruled out for being identical
                    if comp_value == value:
                        num_ruled_out = num_ruled_out + 1
                        continue            
                    # check how many values are ruled out for not matching overlap characters
                    vars_overlap_index = self.crossword.overlaps[(var, neighbor_var)]
                    try:
                        if value[vars_overlap_index[0]] != comp_value[vars_overlap_index[1]]:
                            num_ruled_out = num_ruled_out + 1
                    except IndexError:
                        num_ruled_out = num_ruled_out + 1


            # add the variable with its elimination count to the dictionary
            value_elimination_dict[value] = num_ruled_out

        sorted_dict_list = sorted(value_elimination_dict, key=value_elimination_dict.get)
        return sorted_dict_list

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        for var in assignment:
            if assignment[var] == None:
                return var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # if given an empty assignment, create a new one
        if len(assignment) == 0:
            for var in self.crossword.variables:
                assignment[var] = None

        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            # check if value is cosistent with the constraints
            deep_copy_assignment = copy.deepcopy(assignment)
            deep_copy_assignment[var] = value
            if self.consistent(deep_copy_assignment):
                assignment[var] = value
                result = self.backtrack(assignment)
                if result != None:
                    return result
                
                # if result is a failure, remove it from the assignment
                assignment[var] = None
        # if gone through every var, and no satisfying assignment possible,
        # return None
        return None

            


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
